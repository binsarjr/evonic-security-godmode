# Evonic Security Godmode

Plugin eksternal untuk **authorized LLM red-team testing** di Evonic. Proyek ini
terinspirasi oleh konsep Security Godmode milik Hermes Agent, tetapi merupakan
implementasi clean-room khusus API plugin Evonic—tanpa menyalin template jailbreak
atau memodifikasi core Evonic.

Plugin menyediakan:

- `godmode_transform`: membuat varian prompt deterministik (leet, homoglyph,
  base64, hex, zero-width, dan lain-lain) tanpa mengeksekusinya.
- `godmode_score`: menilai refusal, hedging, struktur, detail, dan latency.
- `godmode_race`: menjalankan prompt pada beberapa model Evonic secara paralel,
  lalu mengurutkan hasilnya. Setiap panggilan dapat memakai kuota provider.
- `godmode_profile`: mengaktifkan konteks red-team per agent, dengan strategi
  `audit`, `refusal_inversion`, `boundary_test`, atau `prefill_simulation`.

## Persyaratan

- Evonic yang mendukung plugin `plugin.json`, `tools_file`, dan turn-context hook.
- Minimal satu model LLM aktif untuk memakai `godmode_race`.
- `zip` hanya diperlukan bila ingin membangun paket release sendiri.

## Instalasi tercepat dari release

Unduh `security-godmode.zip` dari halaman Releases, lalu:

```bash
evonic plugin install "$(pwd)/security-godmode.zip"
evonic plugin enable security_godmode
```

Gunakan path absolut seperti di atas karena beberapa versi CLI Evonic berpindah
ke direktori instalasinya sebelum memproses argumen path.

Atau impor file ZIP melalui halaman **Plugins** pada UI Evonic, lalu aktifkan
**Security Godmode — LLM Red-Team Lab**.

## Instalasi langsung dari source

```bash
git clone https://github.com/binsarjr/evonic-security-godmode.git
cd evonic-security-godmode
EVONIC_BIN=/path/ke/evonic ./scripts/install.sh
```

Untuk instalasi Evonic standar, biasanya cukup:

```bash
./scripts/install.sh
```

Plugin disalin ke instalasi Evonic. Repository ini tetap terpisah sehingga dapat
dikembangkan dan di-versioning tanpa membuat fork core Evonic.

## Memasang tool ke agent

1. Pastikan plugin sudah **enabled** di halaman Plugins.
2. Buka konfigurasi agent Evonic.
3. Di bagian Tools/Plugins, pilih empat tool dengan prefix `godmode_`.
4. Simpan agent.
5. Minta agent memanggil:

```text
godmode_profile(action="enable", strategy="audit")
```

Profil bersifat **opt-in per agent**. Plugin yang aktif secara global belum
menambahkan konteks apa pun sampai profil agent tersebut diaktifkan.

Contoh penggunaan natural-language:

```text
Aktifkan godmode_profile dengan strategi boundary_test untuk agent ini.
Buat varian standard dari prompt berikut dengan godmode_transform: ...
Bandingkan prompt evaluasi ini pada model id A dan B menggunakan godmode_race.
```

Untuk berhenti atau menghapus konfigurasi agent:

```text
godmode_profile(action="disable")
godmode_profile(action="undo")
```

## Apakah ini memakai `import` Evonic?

Ya. ZIP/direktori ini diimpor oleh plugin loader Evonic. `plugin.json` mendaftarkan
empat tool, sedangkan `handler.py` mendaftarkan turn-context provider saat plugin
diaktifkan. Tidak perlu menambah import Python ke source Evonic dan tidak perlu
menambal branch `binsar/dev`.

Evonic saat ini tidak menyediakan hook publik untuk menyisipkan assistant-prefill
mentah sebelum pesan pertama. Karena itu mode `prefill_simulation` menerapkan
priming sebagai system context yang terkontrol. Efeknya serupa untuk pengujian
instruction hierarchy, tetapi tidak mengklaim mampu melewati HMADS atau safeguard
provider.

## Build paket

```bash
./scripts/package.sh
```

Hasilnya tersedia di `dist/security-godmode.zip` dan
`dist/security-godmode.evop`. Keduanya berisi payload yang sama; format ZIP adalah
format instalasi yang didukung resmi oleh CLI Evonic saat ini.

## Pengembangan dan pengujian

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q plugin
```

Setelah mengubah source, jalankan kembali instalasi. Bila versi yang sama sudah
terpasang, hapus plugin dari UI/CLI lebih dahulu atau naikkan `version` pada
`plugin/plugin.json`, sesuai perilaku versi Evonic yang Anda gunakan.

## Batasan dan keamanan

Gunakan hanya pada target yang Anda miliki atau telah mengizinkan pengujian.
Plugin tidak menonaktifkan HMADS, kebijakan model, sandbox, maupun proteksi
provider. Multi-model race dapat menghabiskan kuota dengan cepat dan dibatasi
maksimal 10 model per panggilan serta 5 worker paralel.

Lisensi: MIT.
