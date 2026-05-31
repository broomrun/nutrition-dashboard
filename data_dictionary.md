# Data Dictionary

## Project Overview

Project ini menggunakan beberapa dataset nutrisi makanan dan standar kebutuhan gizi untuk mendukung analisis nutrisi serta pengembangan sistem rekomendasi makanan.

---

# Dataset Sources

## 1. AKG Dataset

### Source

* PERATURAN MENTERI KESEHATAN REPUBLIK INDONESIA NOMOR 28 TAHUN 2019
* Tentang Angka Kecukupan Gizi yang Dianjurkan untuk Masyarakat Indonesia

Link Source:
https://share.google/rFbpKcYvBTttL5yYa

---

### Description

Dataset AKG digunakan sebagai acuan kebutuhan nutrisi harian pengguna berdasarkan profil individu. Profil yang digunakan meliputi usia, jenis kelamin, serta kondisi khusus seperti kehamilan dan menyusui.

Dalam project ini, data AKG digunakan untuk menghitung estimasi kebutuhan nutrisi harian pengguna. Hasil perhitungan tersebut kemudian dibandingkan dengan makanan yang ditambahkan ke dalam food log. Perbandingan ini membantu pengguna melihat sejauh mana konsumsi hariannya telah memenuhi kebutuhan nutrisi berdasarkan standar AKG.

Dataset AKG dibagi menjadi tiga bagian utama:

- `akg_normal`
- `akg_pregnant`
- `akg_breastfeeding`

Pemisahan dataset dilakukan untuk mempermudah proses perhitungan kebutuhan nutrisi berdasarkan kondisi pengguna.

---

## Table: `akg_normal`

### Description

Dataset `akg_normal` berisi kebutuhan nutrisi harian normal untuk individu berdasarkan kelompok usia dan jenis kelamin. Dataset ini digunakan sebagai kebutuhan dasar sebelum ada penambahan kebutuhan pada kondisi khusus seperti kehamilan atau menyusui.

Kategori individu dalam dataset ini meliputi:

- infants & children
- male
- female

Dataset ini tidak mencakup tambahan kebutuhan nutrisi untuk kondisi kehamilan dan menyusui.

### Columns

| Column Name | Data Type | Description | Unit | Example |
|---|---|---|---|---|
| `age_category` | object | Kategori individu berdasarkan usia dan jenis kelamin | - | male |
| `age_group` | object | Rentang usia individu | - | 19-29 years |
| `min_age` | float | Usia minimum pada kelompok usia | year | 19 |
| `max_age` | float | Usia maksimum pada kelompok usia | year | 29 |
| `body_weight` | float | Berat badan acuan berdasarkan standar AKG | kg | 60 |
| `height` | float | Tinggi badan acuan berdasarkan standar AKG | cm | 168 |
| `calories` | integer | Kebutuhan energi harian | kcal | 2650 |
| `protein` | integer | Kebutuhan protein harian | gram | 65 |
| `fat` | float | Kebutuhan lemak harian | gram | 75 |
| `carbs` | integer | Kebutuhan karbohidrat harian | gram | 430 |
| `fiber` | float | Kebutuhan serat harian | gram | 37 |
| `calcium` | float | Kebutuhan kalsium harian | mg | 1000 |
| `iron` | float | Kebutuhan zat besi harian | mg | 9 |
| `vitamin_c` | float | Kebutuhan vitamin C harian | mg | 90 |

### Additional Notes

- `age_category` terdiri dari `infants_children`, `male`, dan `female`.
- Seluruh nilai nutrisi pada tabel ini merepresentasikan kebutuhan harian.
- Data ini menjadi acuan utama dalam perhitungan kebutuhan nutrisi pengguna pada dashboard.
- Jika pengguna memiliki kondisi khusus seperti hamil atau menyusui, nilai dari tabel ini akan ditambahkan dengan nilai tambahan dari tabel `akg_pregnant` atau `akg_breastfeeding`.

---

## Table: `akg_pregnant`

### Description

Dataset `akg_pregnant` berisi tambahan kebutuhan nutrisi harian untuk wanita hamil berdasarkan periode kehamilan. Nilai pada tabel ini bukan kebutuhan total, melainkan tambahan kebutuhan yang akan dijumlahkan dengan kebutuhan dasar wanita sesuai usia pada tabel `akg_normal`.

Contoh:

- wanita usia 19-29 tahun memiliki kebutuhan dasar dari tabel `akg_normal`,
- jika pengguna berada pada kondisi hamil, maka kebutuhan dasarnya akan ditambah dengan nilai tambahan dari tabel `akg_pregnant` sesuai bulan kehamilan.

### Columns

| Column Name | Data Type | Description | Unit | Example |
|---|---|---|---|---|
| `preg_month_min` | integer | Bulan minimum periode kehamilan | month | 1 |
| `preg_month_max` | integer | Bulan maksimum periode kehamilan | month | 3 |
| `calories` | integer | Tambahan kebutuhan energi harian | kcal | 180 |
| `protein` | integer | Tambahan kebutuhan protein harian | gram | 1 |
| `fat` | float | Tambahan kebutuhan lemak harian | gram | 2.3 |
| `carbs` | integer | Tambahan kebutuhan karbohidrat harian | gram | 25 |
| `fiber` | float | Tambahan kebutuhan serat harian | gram | 3 |
| `calcium` | float | Tambahan kebutuhan kalsium harian | mg | 0 |
| `iron` | float | Tambahan kebutuhan zat besi harian | mg | 0 |
| `vitamin_c` | float | Tambahan kebutuhan vitamin C harian | mg | 10 |

### Additional Notes

- Dataset ini hanya digunakan jika pengguna memilih kondisi `Pregnant`.
- Kolom `preg_month_min` dan `preg_month_max` digunakan untuk menentukan tambahan kebutuhan berdasarkan bulan kehamilan.
- Nilai nutrisi pada tabel ini akan dijumlahkan dengan kebutuhan dasar dari tabel `akg_normal`.
- Dataset ini membantu dashboard menghasilkan estimasi kebutuhan nutrisi yang lebih sesuai untuk pengguna dalam kondisi hamil.

---

## Table: `akg_breastfeeding`

### Description

Dataset `akg_breastfeeding` berisi tambahan kebutuhan nutrisi harian untuk wanita menyusui berdasarkan periode menyusui. Sama seperti tabel `akg_pregnant`, nilai pada tabel ini merupakan tambahan kebutuhan, bukan kebutuhan total.

Nilai tambahan dari tabel ini akan dijumlahkan dengan kebutuhan dasar wanita berdasarkan usia pada tabel `akg_normal`.

### Columns

| Column Name | Data Type | Description | Unit | Example |
|---|---|---|---|---|
| `bf_month_min` | integer | Bulan minimum periode menyusui | month | 1 |
| `bf_month_max` | integer | Bulan maksimum periode menyusui | month | 6 |
| `calories` | integer | Tambahan kebutuhan energi harian | kcal | 330 |
| `protein` | integer | Tambahan kebutuhan protein harian | gram | 20 |
| `fat` | float | Tambahan kebutuhan lemak harian | gram | 2.2 |
| `carbs` | integer | Tambahan kebutuhan karbohidrat harian | gram | 45 |
| `fiber` | float | Tambahan kebutuhan serat harian | gram | 5 |
| `calcium` | float | Tambahan kebutuhan kalsium harian | mg | 200 |
| `iron` | float | Tambahan kebutuhan zat besi harian | mg | 0 |
| `vitamin_c` | float | Tambahan kebutuhan vitamin C harian | mg | 45 |

### Additional Notes

- Dataset ini hanya digunakan jika pengguna memilih kondisi `Breastfeeding`.
- Kolom `bf_month_min` dan `bf_month_max` digunakan untuk menentukan tambahan kebutuhan berdasarkan bulan menyusui.
- Nilai nutrisi pada tabel ini akan dijumlahkan dengan kebutuhan dasar dari tabel `akg_normal`.
- Dataset ini membantu dashboard menyesuaikan estimasi kebutuhan nutrisi untuk pengguna dalam kondisi menyusui.

---

## AKG Dataset Usage in Dashboard

Dalam dashboard, data AKG digunakan untuk menghitung kebutuhan nutrisi harian pengguna berdasarkan input profil. Input yang digunakan meliputi:

- nama pengguna,
- jenis kelamin,
- usia,
- kondisi khusus,
- bulan kehamilan atau menyusui jika ada.

Setelah kebutuhan nutrisi dihitung, dashboard membandingkannya dengan total nutrisi dari makanan yang ditambahkan pengguna ke dalam food log.

Nutrisi yang dibandingkan meliputi:

- `calories`
- `protein`
- `fat`
- `carbs`
- `fiber`
- `calcium`
- `iron`
- `vitamin_c`

Hasil perbandingan tersebut ditampilkan dalam bentuk persentase pemenuhan kebutuhan harian, progress bar, dan insight sederhana mengenai kondisi pemenuhan nutrisi pengguna.

## Description

Dataset AKG digunakan sebagai acuan kebutuhan nutrisi harian berdasarkan:

* usia,
* jenis kelamin,
* kondisi kehamilan,
* kondisi menyusui.

Dataset kemudian dipisahkan menjadi:

* `akg_normal`
* `akg_pregnant`
* `akg_breastfeeding`

Pemisahan dilakukan untuk mempermudah proses perhitungan kebutuhan nutrisi berdasarkan kondisi pengguna.

---

# Dataset: `nutrition_table_internal.csv`
# Dataset: `nutrition_table_cleaned.csv`

## Source

Link Source:
https://huggingface.co/datasets/ethz/food101

---

## Description

Dataset Food101 merupakan dataset klasifikasi gambar makanan yang terdiri dari 101 kategori makanan dengan total 101.000 gambar. Setiap kategori memiliki 1.000 gambar makanan.

Pada penelitian ini, dataset digunakan untuk:

* klasifikasi gambar makanan,
* analisis nutrisi makanan,
* pengembangan sistem rekomendasi makanan.

Informasi nutrisi tidak tersedia secara langsung pada dataset asli, sehingga nilai nutrisi dihasilkan (*generated data*) berdasarkan nama kelas makanan (`class_name`).

---

## Dataset Information

| Information      | Value                     |
| ---------------- | ------------------------- |
| Total Classes    | 101                       |
| Total Images     | 101000                    |
| Images per Class | 1000                      |
| Main Data        | Food Images + Food Labels |

---

## Columns

| Column Name   | Data Type | Description                    | Unit | Example    |
| ------------- | --------- | ------------------------------ | ---- | ---------- |
| class_name    | object    | Label atau nama makanan        | -    | apple_pie  |
| calories_kcal | float     | Estimasi kandungan kalori      | kcal | 357.902410 |
| protein_g     | float     | Estimasi kandungan protein     | gram | 6.156793   |
| carbs_g       | float     | Estimasi kandungan karbohidrat | gram | 52.446370  |
| fat_g         | float     | Estimasi kandungan lemak       | gram | 15.864860  |
| fiber_g       | float     | Estimasi kandungan serat       | gram | 1.591933   |
| calcium_mg    | float     | Estimasi kandungan kalsium     | mg   | 89.001382  |
| iron_mg       | float     | Estimasi kandungan zat besi    | mg   | 101.321556 |
| vitamin_c_mg  | float     | Estimasi kandungan vitamin C   | mg   | 2.588036   |

---

## Additional Notes

* Dataset asli Food101 hanya menyediakan gambar makanan dan label kelas.
* Informasi nutrisi dihasilkan berdasarkan nama makanan (`class_name`) menggunakan proses data generation.
* Nilai nutrisi direpresentasikan dalam estimasi per 100 gram makanan.

---

# Dataset: `fooddataset.csv`

### Source

Dataset nutrisi makanan pada project ini berasal dari beberapa sumber, yaitu:

- **Open Nutrition Dataset**
- **Tabel Komposisi Pangan Indonesia (TKPI) 2017**

---

### Description

Dataset ini digunakan sebagai sumber data nutrisi makanan pada dashboard. Data ini berisi informasi kandungan nutrisi dari berbagai jenis makanan dalam satuan per 100 gram.

Dalam project ini, dataset digunakan pada fitur pencarian makanan dan pengecekan kandungan nutrisi. Pengguna dapat mencari nama makanan tertentu, kemudian dashboard akan menampilkan kandungan nutrisi makanan tersebut berdasarkan porsi yang dimasukkan.

Dataset ini juga digunakan untuk mendukung fitur:

- pencarian makanan berdasarkan kategori atau nama makanan,
- pengecekan nutrisi makanan per 100 gram,
- perhitungan nutrisi berdasarkan porsi makanan,
- pencatatan makanan ke dalam food log,
- perbandingan konsumsi makanan dengan kebutuhan AKG pengguna.

---

## Dataset: `fooddataset.csv`

### Dataset Information

| Information | Value |
|---|---|
| Total Rows | 9511 |
| Total Columns | 36 |
| Main Data | Food nutrition per 100 gram |
| Usage | Food search, nutrition checking, and food log calculation |

---

### Columns

| Column Name | Data Type | Description | Unit | Example |
|---|---|---|---|---|
| `foodname_100g` | object | Nama makanan dalam satuan acuan 100 gram | - | Chicken Breast, Boneless Skinless, Cooked |
| `calories` | float | Kandungan energi makanan | kcal | 151.0 |
| `protein` | float | Kandungan protein makanan | gram | 30.54 |
| `total_fat` | float | Kandungan lemak total makanan | gram | 3.17 |
| `omega_3` | float | Kandungan asam lemak omega-3 | gram | 0.047 |
| `omega_6` | float | Kandungan asam lemak omega-6 | gram | 0.705 |
| `carbohydrates` | float | Kandungan karbohidrat makanan | gram | 0.0 |
| `dietary_fiber` | float | Kandungan serat makanan | gram | 0.0 |
| `water` | float | Kandungan air pada makanan | gram | 66.1 |
| `vitamin_d` | float | Kandungan vitamin D | mcg | 1.0 |
| `vitamin_e` | float | Kandungan vitamin E | mg | 0.54 |
| `vitamin_k` | float | Kandungan vitamin K | mcg | 4.3 |
| `thiamin` | float | Kandungan vitamin B1 atau thiamin | mg | 0.107 |
| `riboflavin` | float | Kandungan vitamin B2 atau riboflavin | mg | 0.213 |
| `niacin` | float | Kandungan vitamin B3 atau niacin | mg | 12.133 |
| `pantothenic_acid` | float | Kandungan vitamin B5 atau pantothenic acid | mg | 1.71 |
| `vitamin_b6` | float | Kandungan vitamin B6 | mg | 1.157 |
| `folate_dfe` | float | Kandungan folat dalam satuan DFE | mcg | 4.0 |
| `vitamin_b12` | float | Kandungan vitamin B12 | mcg | 0.21 |
| `biotin` | float | Kandungan biotin | mcg | 0.0 |
| `choline` | float | Kandungan choline | mg | 111.0 |
| `vitamin_c` | float | Kandungan vitamin C | mg | 0.0 |
| `calcium` | float | Kandungan kalsium | mg | 5.0 |
| `phosphorus` | float | Kandungan fosfor | mg | 258.0 |
| `magnesium` | float | Kandungan magnesium | mg | 34.0 |
| `iron` | float | Kandungan zat besi | mg | 0.45 |
| `iodine` | float | Kandungan iodine | mcg | 0.0 |
| `zinc` | float | Kandungan zinc | mg | 0.9 |
| `selenium` | float | Kandungan selenium | mcg | 28.4 |
| `manganese` | float | Kandungan mangan | mg | 0.012 |
| `chromium` | float | Kandungan chromium | mcg | 0.0 |
| `potassium` | float | Kandungan kalium | mg | 391.0 |
| `sodium` | float | Kandungan natrium | mg | 52.0 |
| `chlorine` | float | Kandungan chlorine | mg | 0.0 |
| `copper` | float | Kandungan tembaga | mg | 0.042 |
| `vitamin_a` | float | Kandungan vitamin A | mcg | 10.0 |

---

### Usage in Dashboard

Pada dashboard, dataset ini digunakan untuk menyediakan informasi nutrisi makanan yang dapat dicari oleh pengguna. Pengguna dapat memilih atau mencari makanan tertentu, kemudian memasukkan ukuran porsi dalam gram.

Setelah porsi dimasukkan, dashboard akan menghitung kandungan nutrisi makanan menggunakan rumus:

`nutrition_per_portion = nutrition_per_100g × portion_gram / 100`

Hasil perhitungan ini digunakan pada fitur:

- **Check Food Nutrition by Portion**, untuk melihat kandungan nutrisi makanan berdasarkan porsi tertentu.
- **Added Food Today**, untuk menambahkan makanan ke dalam food log harian.
- **Food Log Table**, untuk mencatat total makanan yang sudah ditambahkan pengguna.
- **Daily Nutrition Progress**, untuk membandingkan total konsumsi dengan kebutuhan AKG pengguna.

---

### Additional Notes

- Dataset ini merepresentasikan nilai nutrisi makanan per 100 gram.
- Data dari OpenNutrition dan TKPI 2017 digunakan sebagai referensi komposisi nutrisi makanan.
- Kolom `foodname_100g` digunakan sebagai nama makanan utama dalam fitur pencarian.
- Beberapa nama kolom disesuaikan pada tahap preprocessing agar konsisten dengan format dashboard.
- Dataset ini membantu pengguna mengetahui kandungan nutrisi makanan secara lebih praktis melalui fitur pencarian dan pengecekan porsi.


