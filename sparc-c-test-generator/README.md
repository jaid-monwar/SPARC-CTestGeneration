# SPARC-CTestGeneration

AI-powered C unit test generation using static analysis (CFG + execution paths) and LLM-based test synthesis with iterative validation.

```
Source Code → CFG Analysis → Execution Paths → AI Test Generation → Validation → Compiled Tests
```

---

## Setup

### Prerequisites

- **API key** for at least one LLM provider — set in a `.env` file in the project root:

```env
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
```

> Only the key for the provider you intend to use is required.

---

## Method 1 — Docker (recommended)

No local Python setup required. Docker handles all system and Python dependencies.

### Build the image

```bash
# First time or after Dockerfile changes (no cache):
docker build --no-cache -t ctestgen .

# Subsequent builds (uses cache):
docker build -t ctestgen .
```

### Run the pipeline

The general form mounts the project directory and passes your `.env` file into the container:

```bash
docker run --rm -v $(pwd):/workspace --env-file .env ctestgen \
  ./test/scripts/run_tests.sh <subject> test/projects <operations> <create_embed> <architecture> <per_function> <model>
```

**Examples:**

```bash
# GPT — build FAISS embeddings on first run (create_embed=true)
docker run --rm -v $(pwd):/workspace --env-file .env ctestgen \
  ./test/scripts/run_tests.sh qsort test/projects all true monolithic true gpt

# GPT — reuse existing embeddings (create_embed=false)
docker run --rm -v $(pwd):/workspace --env-file .env ctestgen \
  ./test/scripts/run_tests.sh qsort test/projects all false monolithic true gpt

# DeepSeek
docker run --rm -v $(pwd):/workspace --env-file .env ctestgen \
  ./test/scripts/run_tests.sh qsort test/projects all false monolithic true deepseek

# Gemini
docker run --rm -v $(pwd):/workspace --env-file .env ctestgen \
  ./test/scripts/run_tests.sh buffer test/projects all false monolithic true gemini
```

**Algorithm subjects** (C2Rust-translated from TheAlgorithms/C):

```bash
docker run --rm -v $(pwd):/workspace --env-file .env ctestgen \
  ./test/scripts/algorithms_run_tests.sh ds_avl_tree test/projects all false monolithic true deepseek
```

---

## Method 2 — Python venv

### 1. System dependencies

```bash
# Ubuntu/Debian
sudo apt-get install gcc clang-18 libclang-18-dev python3-clang-18 lcov graphviz
```

### 2. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Run `source .venv/bin/activate` at the start of every session.

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the pipeline

```bash
source .venv/bin/activate

# Gemini — build FAISS embeddings on first run (create_embed=true)
./test/scripts/run_tests.sh buffer test/projects all true monolithic true gemini

# GPT — reuse existing embeddings on subsequent runs (create_embed=false)
./test/scripts/run_tests.sh buffer test/projects all false monolithic true gpt
```

---

## Arguments

```
./test/scripts/run_tests.sh <subject> <output_dir> <operations> <create_embed> <architecture> <per_function> <model> [max_workers] [max_iterations]
```

| Argument | Values | Description |
|---|---|---|
| `subject` | `bst`, `qsort`, `rgba`, `buffer`, `genann`, `url_parser`, … | C source to test |
| `output_dir` | path | Output directory (typically `test/projects`) |
| `operations` | `all`, `3-7`, `4,8,9`, `5+`, `compile`, `run`, `coverage`, `info` | Which pipeline steps to run |
| `create_embed` | `true` / `false` | Build and populate FAISS vector DB for helper function RAG matching. Use `true` on first run, `false` to reuse existing embeddings |
| `per_function` | `true` / `false` | Validate and merge tests per function (recommended: `true`) |
| `model` | `gpt` / `gemini` / `deepseek` | LLM provider |
| `max_workers` | integer (default: `10`) | Parallel workers for generation |
| `max_iterations` | integer (default: `3`) | Max validation iterations per function |

---

## Supported Subjects

**Primary** (`run_tests.sh`): `bst`, `qsort`, `rgba`, `buffer`, `small-buffer`, `genann`, `url_parser`, `quadtree`, `grabc`, `xzoom`

**Algorithm** (`algorithms_run_tests.sh`): 40+ C2Rust-translated subjects — run the script with no arguments for the full list.

---


