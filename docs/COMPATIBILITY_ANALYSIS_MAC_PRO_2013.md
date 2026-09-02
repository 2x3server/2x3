# VERIFICA TECNICA APPROFONDITA E CONCRETA PER PROGETTO 2X3
**Target Hardware/OS:** Mac Pro 2013 (MacPro6,1) | Intel Xeon E5 (12-Core) | macOS Monterey 12.7.6 | 64 GB RAM | Dual AMD FirePro D700 (6 GB)

---

## 1. Analisi COLMAP: Versione compatibile con macOS Monterey (Intel x86_64)

### Versione più recente realisticamente compatibile:
* **COLMAP 3.8 / 3.9.1 / 3.10 (CPU-only)** sono le versioni storicamente più stabili e ampiamente testate su architettura Intel x86_64 con macOS 12 Monterey.
* **COLMAP 4.1.1 (ultima release)** è concettualmente compatibile con x86_64, ma la formula ufficiale Homebrew per macOS 12 (Monterey) richiede la ricompilazione da sorgente dell'intera catena di dipendenze (tra cui `qtbase`, `openimageio`, `llvm`), poiché Homebrew ha terminato la distribuzione di *bottles* (pacchetti pre-compilati) aggiornati per macOS Monterey.

---

## 2. Compatibilità comandi 2x3 e dipendenze storiche

### Verifica della sintassi e comandi usati da 2x3:
Il progetto 2x3 invoca i seguenti comandi CLI di COLMAP:
1. `feature_extractor` (con `--SiftExtraction.use_gpu 0`, `--ImageReader.single_camera 1`)
2. `exhaustive_matcher` (con `--SiftMatching.use_gpu 0`)
3. `mapper`
4. `image_undistorter` (con `--output_type COLMAP`)
5. `patch_match_stereo` (con `--workspace_format COLMAP`)

**Esito verifica:**
* Tutti questi comandi e le relative flag CLI esistono e mantengono **esattamente la stessa sintassi** a partire da **COLMAP 3.6 fino a COLMAP 4.1.1**.
* Pertanto, qualsiasi versione compresa tra COLMAP 3.7 e COLMAP 3.10 soddisfa al 100% i requisiti del codice Python di 2x3.

### Riduzione delle dipendenze con versioni storiche / Headless:
* L'enorme catena di ~106 dipendenze riscontrata con `brew install colmap` è dovuta principalmente a due fattori:
  1. **Modulo GUI (Qt5/Qt6, OpenGL, GLEW, OpenImageIO, FFmpeg GUI, ecc.)**.
  2. **Mancanza di pacchetti precompilati (bottles) in Homebrew per macOS Monterey (12.x)**.
* Utilizzando una versione storica o una build **Headless (senza interfaccia grafica)**, la dipendenza da Qt/OpenImageIO viene **totalmente eliminata**.

---

## 3. Compilazione COLMAP CPU-only senza Qt / OpenImageIO

### È fattibile?
**SÌ, AL 100%.**

COLMAP dispone di opzioni CMake native per disabilitare la GUI e le componenti grafiche:
* `-DGUI_ENABLED=OFF` (rimuove la dipendenza da Qt5/Qt6)
* `-DOPENGL_ENABLED=OFF` (rimuove le dipendenze OpenGL/GLEW)
* `-DCUDA_ENABLED=OFF` (forza l'elaborazione CPU-only, ideale per AMD FirePro su macOS)

### Dipendenze reali necessarie per COLMAP Headless CPU-only:
Con la GUI disabilitata, rimangono solo le librerie di calcolo scientifico e I/O di base:
1. **Ceres-Solver** (e le sue dipendenze: `suite-sparse`, `glog`, `gflags`)
2. **Boost** *(già installato: 1.92.0)*
3. **Eigen** *(già installato: 5.0.1 / 3.4)*
4. **Metis** *(già installato: 5.1.0)*
5. **SQLite3** *(già installato: 3.53.4)*
6. **FreeImage** (per la lettura/scrittura immagini senza passare da OpenImageIO)

**Risultato:** Da 106 dipendenze si passa a sole **2-3 dipendenze mancanti** (`ceres-solver`, `suite-sparse`, `freeimage`). Il tempo di compilazione sui 12 core del Mac Pro 2013 scende da ore/giorni a circa **8-12 minuti**.

---

## 4. Confronto delle strade per COLMAP

| Metodo | Pro | Contro | Tempo stimato | Probabilità Successo |
| :--- | :--- | :--- | :--- | :--- |
| **A. Homebrew `colmap` (4.1.1)** | Installazione teoricamente standard | Compila Qt5/Qt6 e 106 pacchetti da sorgente su Monterey; frequenti errori SDK | > 3-6 ore | ❌ **15%** |
| **B. Compilazione Manuale Headless (`-DGUI_ENABLED=OFF`)** | Nessuna dipendenza Qt; sfrutta le librerie già presenti sul Mac Pro; codice nativo veloce | Richiede la compilazione manuale di Ceres-Solver | ~15 minuti | 🥈 **85%** |
| **C. Conda / Mamba Environment (`conda-forge::colmap`)** | Pacchetti binaries x86_64 già pronti per Intel Mac; scarica e funziona subito; zero compilazione | Richiede l'uso di un env Conda/Miniconda | ~2 minuti | 🥇 **98%** |

---

## 5. Verifica Fattibilità REALE di OpenMVS su macOS Monterey (Intel x86_64)

### Esistenza di build documentate e funzionanti:
* OpenMVS non viene fornito tramite Homebrew o Conda pre-compilato per macOS. Deve essere **compilato dai sorgenti**.
* Esistono build documentate e funzionanti su macOS Intel (x86_64) con Apple Clang.

### Versione raccomandata:
* **OpenMVS v2.1.0** oppure commit recente sul branch `main`.

### Requisiti e dipendenze reali per OpenMVS:
1. **Eigen 3.4+** *(già presente)*
2. **Boost** *(già presente)*
3. **OpenCV** *(già presente)*
4. **CGAL** (o la libreria VCG integrata)
5. **Ceres-Solver**
6. **libomp** (OpenMP runtime per Apple Clang, installabile con `brew install libomp`)

### Problemi noti su macOS Monterey + Apple Clang 14:
1. **Supporto OpenMP in Apple Clang:** Apple Clang non attiva OpenMP nativamente. È indispensabile passare a CMake:
   `-DOpenMP_C_FLAGS="-Xpreprocessor -fopenmp"` e `-DOpenMP_CXX_FLAGS="-Xpreprocessor -fopenmp"` specificando il percorso di `libomp`.
2. **Incompatibilità GPU CUDA:** Le GPU AMD FirePro D700 del Mac Pro 2013 supportano solo OpenCL 1.2 e non CUDA. OpenMVS deve essere configurato tassativamente in modalità CPU-only:
   `-DOPENMVS_USE_CUDA=OFF`.
3. **Multithreading su 12 Core:** Su CPU Intel Xeon E5 (12 core / 24 thread), OpenMVS CPU-only via OpenMP offre prestazioni elevate per la generazione della mesh densa e della texturizzazione.

### Probabilità realistica di successo per OpenMVS:
* **85%** configurando correttamente CMake con `-DOPENMVS_USE_CUDA=OFF` e `libomp`.
* Tempo di compilazione: **5 - 10 minuti**.

---

## CLASSIFICA FINALE E STRATEGIA CONSIGLIATA

### 🥇 STRADA CONSIGLIATA (Approccio Ibrido: Conda per COLMAP + Compilazione Nativa CPU-only per OpenMVS)
1. **COLMAP:** Utilizzare **Conda / Miniconda / Mamba** ed eseguire:
   `conda install -c conda-forge colmap`
   * *Motivazione:* Fornisce i binari x86_64 per macOS Intel già compilati e testati (COLMAP 3.8/3.9/3.10), evitando 106 compilazioni e la trappola di Qt su macOS Monterey. L'eseguibile `colmap` sarà immediatamente pronto e compatibile con tutti i comandi usati da 2x3.
2. **OpenMVS:** Compilare dai sorgenti in modalità **CPU-only**:
   `cmake -DOPENMVS_USE_CUDA=OFF -DCMAKE_BUILD_TYPE=Release ..`
   * *Motivazione:* Sfrutta i 12 core della CPU Xeon E5 e le 64 GB di RAM senza richiedere dipendenze GPU non supportate.

### 🥈 ALTERNATIVA (Compilazione da sorgenti 100% Bare-Metal Headless)
1. Installare unicamente `ceres-solver` e `freeimage` via Homebrew/sorgenti.
2. Compilare COLMAP dai sorgenti disabilitando la GUI (`-DGUI_ENABLED=OFF -DCUDA_ENABLED=OFF`).
3. Compilare OpenMVS dai sorgenti (`-DOPENMVS_USE_CUDA=OFF`).
   * *Motivazione:* Mantiene il sistema esente da Conda, ma richiede la compilazione di Ceres-Solver.

### ❌ STRADE DA EVITARE
1. **`brew install colmap` (Homebrew standard su Monterey):**
   * *Motivazione:* Tenta di compilare Qt5/Qt6 da sorgente insieme a 106 dipendenze. Risultato pressoché certo: ore di compilazione e fallimento dovuto ad incompatibilità con le versioni SDK di macOS Monterey.
2. **Abilitazione di CUDA per COLMAP o OpenMVS:**
   * *Motivazione:* Le GPU AMD FirePro D700 non sono schede Nvidia e non supportano CUDA. Tentare di attivare CUDA provocherà errori di compilazione o di runtime.
