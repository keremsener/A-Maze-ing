*This project has been created as part of the 42 curriculum by ksener, yukasaca.*

# A-Maze-ing

## Description

A-Maze-ing, bir yapılandırma dosyasından rastgele labirent üreten Python
projesidir. Program perfect modda iki hücre arasında yalnızca tek yol bulunan
bir labirent; varsayılan non-perfect modda ise birbirinden bağımsız en az iki
döngü içeren, Pac-Man benzeri oynanabilir bir alan üretir. Labirentte yer
uygunsa tamamen kapalı hücrelerden görünür bir `42` deseni bulunur.

Üretilen labirent, duvarları hexadecimal bit maskeleriyle kodlayan bir dosyaya
yazılır. Giriş, çıkış ve BFS ile bulunan en kısa çözüm de bu dosyaya eklenir.
Labirent MiniLib. gösterilir.

## Instructions

### Gereksinimler ve kurulum

Proje Python 3.10 veya üzerini gerektirir. Birlikte verilen MiniLibX paketi
Ubuntu Linux x86_64 içindir. Ubuntu'da gerekli sistem kütüphaneleri şu şekilde
kurulur:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv make \
    libxcb1 libxcb-keysyms1 libvulkan1 zlib1g libbsd0
```

Python bağımlılıklarını, `mazegen` paketini ve MiniLibX'i kurmak için:

```bash
make install
```

### Çalıştırma

Varsayılan yapılandırmayla çalıştırmak için:

```bash
make run
```

Başka bir yapılandırma dosyası kullanmak için:

```bash
make run CONFIG=path/to/config.txt
```

`make install` sonrasında sanal ortam etkinleştirilerek subject'teki CLI
sözleşmesiyle de çalıştırılabilir:

```bash
source .venv/bin/activate
python3 a_maze_ing.py config.txt
```

Program tam olarak bir yapılandırma dosyası argümanı bekler. Üretilen dosyanın
yolu `OUTPUT_FILE` ile belirlenir.

Diğer zorunlu Makefile hedefleri:

```bash
make debug        # Programı pdb ile çalıştırır
make lint         # flake8 ve zorunlu mypy kontrollerini çalıştırır
make clean        # Cache ve geçici build dosyalarını siler
```

Yeniden kullanılabilir paketi kök dizinde oluşturmak için:

```bash
make package
```

## Configuration file

Yapılandırma dosyası her satırda bir `KEY=VALUE` çifti içerir. Boş satırlar ve
ilk anlamlı karakteri `#` olan satırlar yok sayılır. Anahtarlar büyük/küçük
harfe duyarsızdır; anahtar ve değerlerin çevresindeki boşluklar temizlenir.
Aynı anahtar birden fazla kez yazılamaz.

| Anahtar | Zorunluluk | Format ve anlam |
|---|---|---|
| `WIDTH` | Zorunlu | Labirentin hücre cinsinden genişliği; `2..500` arası tam sayı |
| `HEIGHT` | Zorunlu | Labirentin hücre cinsinden yüksekliği; `2..500` arası tam sayı |
| `ENTRY` | Zorunlu | Giriş koordinatı, `x,y` formatında |
| `EXIT` | Zorunlu | Çıkış koordinatı, `x,y` formatında |
| `OUTPUT_FILE` | Zorunlu | Üretilen labirentin yazılacağı dosya yolu |
| `PERFECT` | Zorunlu | `True` ise perfect, `False` ise non-perfect labirent |
| `SEED` | İsteğe bağlı | Tekrarlanabilir üretim için tam sayı; verilmezse rastgele üretim |

`PERFECT` için doğru değerler `true`, `yes`, `on`, `1`; yanlış değerler
`false`, `no`, `off`, `0` olarak kabul edilir. Koordinatlarda `x` sütunu,
`y` satırı gösterir; giriş ve çıkış sınırlar içinde ve birbirinden farklı
olmalıdır.

Varsayılan dosya [packages/configuration/config.txt](packages/configuration/config.txt)
içindedir ve şu yapıdadır:

```ini
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
```

## Maze generation algorithm

Üretim için iterative randomized depth-first search (DFS), yani recursive
backtracker'ın stack kullanan sürümü seçildi. Başlangıçta her hücrenin dört
duvarı da kapalıdır. Algoritma giriş hücresinden başlar, ziyaret edilmemiş ve
`42` desenine ait olmayan rastgele bir komşuya geçerken iki hücre arasındaki
duvarı karşılıklı açar; ilerleyemediğinde stack üzerinden geri döner.

Bu algoritma perfect modda bağlı bir spanning tree üretir. Bir tree döngü
içermediğinden herhangi iki geçilebilir hücre arasında yalnızca tek yol vardır.
DFS'nin seçilme nedenleri basit duvar modeliyle doğrudan çalışması, seed ile
kolayca tekrarlanabilmesi ve perfect labirent koşulunu doğal olarak sağlamasıdır.
Recursive sürüm yerine iterative sürüm kullanılması, büyük labirentlerde Python
recursion limitine takılmayı önler.

Non-perfect modda DFS sonucundaki dead-end hücreler iki geçişte braid edilir.
Ardından graph cycle rank kontrol edilir ve en az iki bağımsız döngü oluşana
kadar uygun kapalı duvarlar açılır. Her açma işleminden önce tamamen açık bir
`3x3` alan oluşturmayacağı doğrulanır. Girişten çıkışa en kısa yol, ağırlıksız
grid üzerinde breadth-first search (BFS) ile bulunur.

## Reusable module

Labirent üretim mantığı `mazegen` paketi olarak sunulur; bunun yanında yapılandırma, 
çıktı yazma ve MiniLibX görünüm katmanları da aynı wheel içinde paketlenir. 
Böylece başka bir yere taşıdığınızda wheel ile birlikte `a_maze_ing.py` kullanmanız 
yeterlidir; varsayılan `config.txt` de wheel'e dahil edilir.

`make package`, kök dizinde daha sonra `pip` ile kurulabilen `mazegen-*.whl` 
dosyasını üretir.

Temel kullanım ve özel boyut/seed geçirme örneği:

```python
from mazegen import MazeError, MazeGenerator

try:
    maze = MazeGenerator(
        width=20,
        height=15,
        entry=(0, 0),
        exit=(19, 14),
        perfect=False,
        seed=42,
    )
    grid = maze.generate()
    path = maze.solve()
    directions = MazeGenerator.coords_to_letters(path)
except MazeError as error:
    print(error)
```

Üretilen yapı `grid[y][x]` ile erişilen `list[list[int]]` biçimindedir. Her
hücrede kapalı duvar bitleri North=`1`, East=`2`, South=`4`, West=`8` olarak
tutulur. `solve()` girişten çıkışa en kısa yolu koordinat listesi olarak;
`coords_to_letters()` ise aynı yolu `N`, `E`, `S`, `W` harfleriyle verir.

## Advanced features and display

- `SEED` ile tekrarlanabilir üretim desteklenir.
- Perfect ve braid edilmiş non-perfect üretim modları bulunur.

- grafik görünümünde `1` yeni labirent üretir, `2` en kısa
  yolu gösterir/gizler, `3` duvar renk temasını değiştirir ve `4` programdan
  çıkar. Grafik görünümünde `Q` ve `Esc` de çıkış yapar.
- `42` deseni ayrı renkle gösterilir.

## Team and project management

### Roller

- **ksener:** maze generator çekirdeği, duvar işlemleri, `42` deseni,
  perfect/non-perfect üretim, BFS solver, yeniden kullanılabilir paket yapısı
  ve Makefile üzerinde çalıştı.
- **yukasaca:** config parser ve doğrulama, hata sınıfları, output writer,
  ortak görünüm modeli, MiniLibX renderer'ları, kullanıcı etkileşimleri
  ve ana program entegrasyonu üzerinde çalıştı.
- **Ortak:** subject kontrolü, lint/type kontrolleri, paketleme doğrulaması ve
  dokümantasyon yürütüldü.

### Planlama ve planın gelişimi

Başlangıç planı işi generator ile uygulama/görselleştirme olarak ikiye bölmekti.
Geliştirme sırasında tek dosyada büyüyen parçalar ayrıldı: solver ve `42`
deseni generator'dan; config, output ve renderer'lar ana programdan bağımsız
modüllere taşındı. Son aşamada `mazegen` kurulabilir bir pakete dönüştürüldü,
MiniLibX kurulumu Ubuntu için Makefile'a eklendi ve seed, mypy ve paketleme
sorunları giderildi.

### Retrospektif

Sorumlulukların modül sınırlarıyla ayrılması, küçük Git commitleri ve ortak
`Scene` modelinin iki renderer tarafından kullanılması iyi çalıştı. Geliştirme
iyileştirilecek olsaydı otomatik testler ve subject'in `maze_analyzer.py`
kontrolleri daha erken kurulabilir, entegrasyon sorunları sona bırakılmadan
daha küçük aralıklarla doğrulanabilirdi.

Kullanılan araçlar: Git, Make, Python virtual environment, MiniLibX, Flake8,
mypy ve build/setuptools.

## Resources

- A-Maze-ing subject v2.2
- [Maze generation algorithms](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Python `random` documentation](https://docs.python.org/3/library/random.html)
- [Python `collections.deque` documentation](https://docs.python.org/3/library/collections.html#collections.deque)
- [Python packaging: Writing your `pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Setuptools package discovery and `src` layout](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#src-layout)
- [Flake8 documentation](https://flake8.pycqa.org/)
- [mypy documentation](https://mypy.readthedocs.io/)
- Repo ile verilen MiniLibX 2.2 dokümantasyonu

AI; subject maddelerini bir kontrol listesine dönüştürmek, edge-case ve graph
invariant senaryoları önermek, paketleme/Makefile sorunlarını teşhis etmek ve
dokümantasyonun ilk taslağını hazırlamak için kullanıldı. Üretilen öneriler
doğrudan kabul edilmedi; kod incelemesi, Flake8, mypy, wheel build/install ve
gerçek CLI çalıştırmalarıyla kontrol edildi.
