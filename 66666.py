from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import argparse
import os
def create_report(text, report_type, output_path):
    # 根据类型选择背景图片和颜色设置
    if report_type == "happy":
        bg_image_path = "good_news.jpg"
        text_color = "red"
        border_color = "yellow"
        shadow_color = "darkred"
    else:  # sad report
        bg_image_path = "bad_news.jpg"
        text_color = "black"
        border_color = "gray"
        shadow_color = "darkgray"
    
    try:
        # 打开背景图片
        image = Image.open(bg_image_path)
    except FileNotFoundError:
        print(f"错误: 找不到背景图片 '{bg_image_path}'")
        return
    
    # 创建一个可绘制对象
    draw = ImageDraw.Draw(image)
    
    # 获取图片尺寸
    width, height = image.size
    
    # 尝试使用中文字体，如果系统没有则使用默认字体
    try:
        # 根据图片大小调整字体大小
        font_size = min(width, height) // 10
        font = ImageFont.truetype(os.path.abspath("./homoossansblack.ttf"), font_size)  # 黑体
    except:
        font = ImageFont.load_default()
        print("警告: 未找到中文字体，使用默认字体")
    
    # 文本换行处理
    avg_char_width = font_size
    max_chars_per_line = width // avg_char_width
    wrapped_text = textwrap.fill(text, width=max_chars_per_line)
    
    # 计算文本位置（居中）
    lines = wrapped_text.split('\n')
    line_heights = [font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines]
    text_height = sum(line_heights)
    
    y = (height - text_height) // 2
    
    # 先绘制阴影
    shadow_offset = font_size // 20
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2 + shadow_offset
        
        # 绘制阴影
        draw.text((x, y + shadow_offset), line, font=font, fill=shadow_color)
        
        # 移动到下一行
        y += line_heights[i]
    
    # 重置y坐标
    y = (height - text_height) // 2
    
    # 绘制文字和边框
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        
        # 先绘制边框（通过多次偏移绘制实现）
        border_width = font_size // 20
        for offset_x in range(-border_width, border_width + 1):
            for offset_y in range(-border_width, border_width + 1):
                if offset_x == 0 and offset_y == 0:
                    continue
                draw.text((x + offset_x, y + offset_y), line, font=font, fill=border_color)
        
        # 然后绘制文字
        draw.text((x, y), line, font=font, fill=text_color)
        
        # 移动到下一行
        y += line_heights[i]
    
    # 保存图片
    image.save(output_path)
    print(f"{'喜报' if report_type == 'happy' else '悲报'}已保存至: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="喜报/悲报生成器")
    parser.add_argument("text", help="要在图片上显示的文字")
    parser.add_argument("--type", choices=["happy", "sad"], default="happy", 
                       help="报告类型: happy(喜报) 或 sad(悲报)，默认为happy")
    parser.add_argument("--output", "-o", default="output.png", 
                       help="输出图片文件名，默认为output.png")
    
    args = parser.parse_args()
    
    create_report(args.text, args.type, args.output)

if __name__ == "__main__":
    # 示例用法（如果直接运行脚本而不是通过命令行）
    # create_report("恭喜发财！", "happy", "喜报示例.png")
    # create_report("很遗憾...", "sad", "悲报示例.png")
    
    main()