import sys
from typing import List, Tuple

try:
    from mlx.mlx import Mlx
except ImportError:
    Mlx = None

class Colors:
    BG = 0xFF1A1A1A            # Koyu Gri (Arka Plan)
    ENTRY = 0xFF2ECC71         # Yeşil (Giriş Noktası)
    EXIT = 0xFFE74C3C          # Kırmızı (Çıkış Noktası)
    PATH = 0xFFF1C40F          # Sarı (Çözüm Yolu)
    
    WALL_PALETTES = [
        0xFFFFFFFF,  # Klasik Beyaz
        0xFF00CED1,  # Camgöbeği
        0xFF00FF00,  # Matrix Yeşili
        0xFFFFD700,  # Altın Sarısı
        0xFFFF4500   # Lav Kırmızısı
    ]
