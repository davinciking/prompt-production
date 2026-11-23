import AppKit
import Foundation

// Usage: swift render_caption_png.swift <output.png> <headline> [sub_badge]
let args = CommandLine.arguments
guard args.count >= 3 else {
    fputs("Usage: swift render_caption_png.swift <output.png> <headline> [sub_badge]\n", stderr)
    exit(1)
}

let outPath = args[1]
let headline = args[2].uppercased()
let subBadge = args.count >= 4 ? args[3].uppercased() : ""

let width = 1080
let height = 1920

guard let bitmap = NSBitmapImageRep(
    bitmapDataPlanes: nil,
    pixelsWide: width,
    pixelsHigh: height,
    bitsPerSample: 8,
    samplesPerPixel: 4,
    hasAlpha: true,
    isPlanar: false,
    colorSpaceName: .deviceRGB,
    bytesPerRow: 0,
    bitsPerPixel: 0
) else {
    fputs("Failed to allocate bitmap\n", stderr)
    exit(1)
}

NSGraphicsContext.saveGraphicsState()
let ctx = NSGraphicsContext(bitmapImageRep: bitmap)
NSGraphicsContext.current = ctx

// Clear transparent canvas
NSColor.clear.setFill()
NSRect(x: 0, y: 0, width: width, height: height).fill()

// Note: AppKit default coords have y=0 at bottom. Safe-zone top headline sits around y_from_top = 200..440
// => AppKit y = height - y_from_top.
var currentTop: CGFloat = 200.0

if !subBadge.isEmpty {
    let badgeFont = NSFont.monospacedSystemFont(ofSize: 28, weight: .bold)
    let badgeAttrs: [NSAttributedString.Key: Any] = [
        .font: badgeFont,
        .foregroundColor: NSColor(calibratedRed: 0.96, green: 0.94, blue: 0.90, alpha: 1.0),
        .kern: 1.5
    ]
    let badgeStr = NSAttributedString(string: subBadge, attributes: badgeAttrs)
    let bSize = badgeStr.size()
    let padX: CGFloat = 24
    let padY: CGFloat = 10
    let boxW = bSize.width + padX * 2
    let boxH = bSize.height + padY * 2
    let boxX = (CGFloat(width) - boxW) / 2.0
    let boxY = CGFloat(height) - currentTop - boxH

    let pillRect = NSRect(x: boxX, y: boxY, width: boxW, height: boxH)
    let pillPath = NSBezierPath(roundedRect: pillRect, xRadius: 10, yRadius: 10)
    NSColor(calibratedRed: 0.06, green: 0.06, blue: 0.07, alpha: 0.84).setFill()
    pillPath.fill()

    NSColor(calibratedRed: 0.85, green: 0.72, blue: 0.42, alpha: 0.55).setStroke()
    pillPath.lineWidth = 2.0
    pillPath.stroke()

    badgeStr.draw(at: NSPoint(x: boxX + padX, y: boxY + padY - 1))
    currentTop += boxH + 18
}

if !headline.isEmpty {
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = .center
    paragraph.lineSpacing = 8

    let shadow = NSShadow()
    shadow.shadowColor = NSColor(calibratedWhite: 0.0, alpha: 0.90)
    shadow.shadowOffset = NSSize(width: 0, height: -4)
    shadow.shadowBlurRadius = 10

    let headFont = NSFont.systemFont(ofSize: 54, weight: .heavy)
    let headAttrs: [NSAttributedString.Key: Any] = [
        .font: headFont,
        .foregroundColor: NSColor.white,
        .strokeColor: NSColor(calibratedWhite: 0.0, alpha: 0.92),
        .strokeWidth: -3.5,
        .paragraphStyle: paragraph,
        .shadow: shadow
    ]
    let headStr = NSAttributedString(string: headline, attributes: headAttrs)
    let maxW: CGFloat = 920
    let bounds = headStr.boundingRect(with: NSSize(width: maxW, height: 400), options: [.usesLineFragmentOrigin, .usesFontLeading])
    let drawRect = NSRect(
        x: (CGFloat(width) - maxW) / 2.0,
        y: CGFloat(height) - currentTop - ceil(bounds.height) - 10,
        width: maxW,
        height: ceil(bounds.height) + 20
    )
    headStr.draw(with: drawRect, options: [.usesLineFragmentOrigin, .usesFontLeading])
}

NSGraphicsContext.restoreGraphicsState()

guard let pngData = bitmap.representation(using: .png, properties: [:]) else {
    fputs("Failed to encode PNG\n", stderr)
    exit(1)
}
do {
    try pngData.write(to: URL(fileURLWithPath: outPath))
} catch {
    fputs("Failed to write PNG: \(error)\n", stderr)
    exit(1)
}
