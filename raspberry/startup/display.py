from PIL import Image, ImageDraw, ImageFont
import board
import busio
import adafruit_ssd1306
import netifaces as ni

WIDTH = 128
HEIGHT = 32


def get_ip() -> str:
    interfaces = ["eth0", "wlan0"]
    for iface in interfaces:
        try:
            ip = ni.ifaddresses(iface)[ni.AF_INET][0]["addr"]
            return ip
        except (KeyError, ValueError):
            continue
    return "couldn't start server\nplease restart device"


def main() -> None:
    i2c = busio.I2C(board.SCL, board.SDA)

    oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)

    oled.fill(0)
    oled.show()

    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    font = ImageFont.load_default()
    ip = get_ip()

    text = "server started at\n" + ip + ":8080"

    with open(
        "/home/raspberry/projects/tactileforce/raspberry/startup/ip.txt", "w"
    ) as f:
        f.write(ip)

    draw.text((20, 5), text, font=font, fill=255)

    oled.image(image)
    oled.show()


if __name__ == "__main__":
    main()
