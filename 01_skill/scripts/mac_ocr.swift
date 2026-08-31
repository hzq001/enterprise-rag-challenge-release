import CoreGraphics
import Darwin
import Foundation
import ImageIO
import Vision

struct OCRLine: Encodable {
    let text: String
    let confidence: Float
    let boundingBox: [Double]
}

struct OCRPage: Encodable {
    let path: String
    let text: String
    let lines: [OCRLine]
    // 始终输出 error 字段，便于 Python 端区分空文本和进程协议异常。
    let error: String
}

struct OCRBatch: Encodable {
    let pages: [OCRPage]
}

func failure(path: String, message: String) -> OCRPage {
    return OCRPage(path: path, text: "", lines: [], error: message)
}

func recognize(path: String) -> OCRPage {
    let url = URL(fileURLWithPath: path)
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        return failure(path: path, message: "无法读取图片")
    }

    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]

    do {
        let handler = VNImageRequestHandler(cgImage: image, options: [:])
        try handler.perform([request])
    } catch {
        return failure(path: path, message: error.localizedDescription)
    }

    let observations = request.results ?? []
    let lines = observations.compactMap { observation -> OCRLine? in
        guard let candidate = observation.topCandidates(1).first else {
            return nil
        }
        return OCRLine(
            text: candidate.string,
            confidence: candidate.confidence,
            boundingBox: [
                Double(observation.boundingBox.origin.x),
                Double(observation.boundingBox.origin.y),
                Double(observation.boundingBox.size.width),
                Double(observation.boundingBox.size.height),
            ]
        )
    }.sorted { left, right in
        // Vision 坐标原点在左下角，所以 y 越大越靠前；同一行再按 x 排序。
        let leftY = left.boundingBox[1]
        let rightY = right.boundingBox[1]
        if abs(leftY - rightY) > 0.01 {
            return leftY > rightY
        }
        return left.boundingBox[0] < right.boundingBox[0]
    }

    return OCRPage(
        path: path,
        text: lines.map(\.text).joined(separator: "\n"),
        lines: lines,
        error: ""
    )
}

let paths = Array(CommandLine.arguments.dropFirst())
guard !paths.isEmpty else {
    fputs("usage: mac_ocr.swift IMAGE...\n", stderr)
    exit(2)
}

let output = OCRBatch(pages: paths.map(recognize))
let encoder = JSONEncoder()
do {
    let data = try encoder.encode(output)
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data("\n".utf8))
} catch {
    fputs("无法编码 OCR 结果: \(error.localizedDescription)\n", stderr)
    exit(3)
}
