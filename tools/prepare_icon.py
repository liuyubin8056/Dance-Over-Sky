"""把「白底线条图」转成透明底 PNG，供游戏当图标用。

用法：

    python tools/prepare_icon.py images/f-16.jpg images/f-16.png
    python tools/prepare_icon.py images/f-16.jpg images/f-16.png --preview images/f-16-preview.png

做的事：

1. 用亮度当「线条浓度」：alpha = 255 - 亮度。白底变全透明，黑线变全不透明，
   抗锯齿留下的灰边保留成半透明，缩到小图标时不会出现白边。
2. 默认把线条统一改成浅色（--line-color）。游戏背景接近纯黑，原来的黑线在深色
   底上几乎是看不见的；想保留原图颜色就加 --keep-color。
3. --preview 会额外生成一张「按游戏内尺寸画在深色底上、再放大」的预览图，
   用来肉眼确认小图标是否还认得出来。

后续加机型时，只要拿到白底（或浅底）线条图，用同一套参数过一遍即可。
"""
from __future__ import annotations

import argparse
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # 本脚本不显示窗口，只处理像素

import pygame


def parse_color(text: str):
    parts = [int(p) for p in text.replace(" ", "").split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("颜色格式应为 r,g,b")
    return tuple(max(0, min(255, p)) for p in parts)


def key_out_white(
    source: pygame.Surface,
    white_threshold: int = 248,
    boost: float = 1.0,
    line_color=None,
) -> pygame.Surface:
    """白底转透明：返回带 alpha 的新 Surface。"""
    width, height = source.get_size()
    result = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        for x in range(width):
            red, green, blue, _ = source.get_at((x, y))
            luminance = (299 * red + 587 * green + 114 * blue) // 1000
            if luminance >= white_threshold:
                alpha = 0
            else:
                alpha = int((255 - luminance) * boost)
                if alpha > 255:
                    alpha = 255
            color = (red, green, blue) if line_color is None else line_color
            result.set_at((x, y), (color[0], color[1], color[2], alpha))
    return result


def write_preview(icon_path: str, out_path: str, icon_size, background, scale: int = 8):
    """把图标按游戏内尺寸画在背景色上再放大，方便检查可读性。"""
    icon = pygame.image.load(icon_path).convert_alpha()
    small = pygame.transform.smoothscale(icon, icon_size)
    surface = pygame.Surface((icon_size[0] * scale, icon_size[1] * scale))
    surface.fill(background)
    surface.blit(pygame.transform.scale(small, surface.get_size()), (0, 0))
    pygame.image.save(surface, out_path)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="白底线条图 -> 透明底 PNG")
    parser.add_argument("source", help="输入图片（白底线条图）")
    parser.add_argument("output", help="输出的 PNG 路径")
    parser.add_argument(
        "--white-threshold",
        type=int,
        default=248,
        help="亮度大于等于该值的像素视为背景，完全透明（默认 248）",
    )
    parser.add_argument(
        "--boost", type=float, default=1.0, help="线条不透明度增益（默认 1.0）"
    )
    parser.add_argument(
        "--line-color",
        type=parse_color,
        default=parse_color("235,240,245"),
        help="线条统一改成这个颜色，格式 r,g,b（默认 235,240,245 浅色）",
    )
    parser.add_argument("--keep-color", action="store_true", help="保留原图颜色")
    parser.add_argument(
        "--crop",
        type=int,
        default=0,
        help="先裁掉四周各 N 像素，用来去掉扫描边、杂点（默认 0）",
    )
    parser.add_argument("--preview", help="额外输出一张放大预览图")
    parser.add_argument("--preview-size", default="50x30", help="预览用的游戏内尺寸")
    args = parser.parse_args()

    pygame.init()
    pygame.display.set_mode((1, 1))  # convert_alpha 需要先有显示模式

    source = pygame.image.load(args.source).convert_alpha()
    if args.crop > 0:
        width, height = source.get_size()
        crop = args.crop
        source = source.subsurface(
            pygame.Rect(crop, crop, width - crop * 2, height - crop * 2)
        ).copy()
    result = key_out_white(
        source,
        white_threshold=args.white_threshold,
        boost=args.boost,
        line_color=None if args.keep_color else args.line_color,
    )
    pygame.image.save(result, args.output)
    print(f"saved {args.output}  {result.get_size()[0]}x{result.get_size()[1]}")

    if args.preview:
        width, height = (int(v) for v in args.preview_size.lower().split("x"))
        write_preview(args.output, args.preview, (width, height), (10, 10, 10))
        print(f"saved {args.preview}")


if __name__ == "__main__":
    main()
