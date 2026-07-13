import os
from typing import Dict, Tuple

class ConfigError(Exception):
    pass

class ConfigParser:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.width = 0
        self.height = 0
        self.entry: Tuple[int, int] = (0, 0)
        self.exit: Tuple[int, int] = (0, 0)
        self.output_file = ""
        self.perfect = 1

        self.parse()

    def parse(self):
        if not os.path.isfile(self.filepath):
            raise ConfigError(f"Hata: '{self.filepath}' dosyası bulunamadı!")

        params: Dict[str, str] = {}
        with open(self.filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                line = line.replace('=', ' ').replace(',', ' ')
                parts = line.split()
                if not parts:
                    continue
                key = parts[0].upper()
                params[key] = " ".join(parts[1:])
        try:
            self.width = int(params.get("WIDTH", "0"))
            self.height = int(params.get("HEIGHT", "0"))
            
            if self.width <= 0 or self.height <= 0:
                raise ConfigError("WIDTH ve HEIGHT sıfırdan büyük pozitif tam sayılar olmalıdır.")

            entry_parts = params.get("ENTRY", "0 0").split()
            if len(entry_parts) != 2:
                raise ConfigError("ENTRY değeri iki tam sayı içermelidir.")
            self.entry = (int(entry_parts[0]), int(entry_parts[1]))

            exit_parts = params.get("EXIT", f"{self.width-1} {self.height-1}").split()
            if len(exit_parts) != 2:
                raise ConfigError ("EXIT değeri iki tam sayı içermelidir.")
            self.exit = (int(exit_parts[0]), int(exit_parts[1]))

            for name, (x, y) in [("ENTRY", self.entry), ("EXIT", self.exit)]:
                if not (0 <= x < self.width and 0 <= y < self.height):
                    raise ConfigError(f"Koordinat {name}({x},{y}) labirent sınırları dışında!")
                
            self.output_file = params.get("OUTPUT_FILE", "maze.dat")
            if not self.output_file:
                raise ConfigError("OUTPUT_FILE belirtilmemiş.")

            perfect_str = params.get("PERFECT", "1").upper()
            if perfect_str in ["1", "TRUE", "T"]:
                self.perfect = 1
            elif perfect_str in ["0", "FALSE", "F"]:
                self.perfect = 0
            else:
                raise ConfigError("PERFECT sadece 0, 1, True veya False olabilir.")

        except ValueError as e:
            raise ConfigError("Yapılandırma dosyasında sayı beklenirken geçersiz bir karakter okundu!") from e

    def __str__(self):
        return (f"Ayar Özeti:\n"
                f"  Boyut: {self.width}x{self.height}\n"
                f"  Giriş: {self.entry}, Çıkış: {self.exit}\n"
                f"  Mükemmel: {'Evet' if self.perfect else 'Hayır'}\n"
                f"  Çıktı Dosyası: {self.output_file}")

if __name__ == "__main__":
    try:
        config = ConfigParser("config.txt")
        print(config)
    except ConfigError as e:
        print(f"Hata yakalandı: {e}")