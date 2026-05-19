FROM ubuntu:22.04

USER root
WORKDIR /workspace

# 1. Try running apt-get update allowing insecure repositories (may fail because the key isn't added yet)
RUN apt-get update --allow-insecure-repositories || true

# 2. Install basic tools without updating apt index (installation may fail but continue anyway)
RUN apt-get install -y --no-install-recommends ca-certificates wget gnupg lsb-release || true

# 3. Import the Kitware public key and convert it to a GPG keyring format
RUN wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc | \
    gpg --dearmor - | tee /usr/share/keyrings/kitware-archive-keyring.gpg > /dev/null

# 4. Add the Kitware repository with signature verification using the imported key
RUN echo "deb [signed-by=/usr/share/keyrings/kitware-archive-keyring.gpg] https://apt.kitware.com/ubuntu/ jammy main" > /etc/apt/sources.list.d/kitware.list

# 5. Add LLVM 18 APT repository and import the GPG key
RUN apt-get install -y ca-certificates gnupg wget lsb-release && \
    wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | gpg --dearmor -o /usr/share/keyrings/llvm.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/llvm.gpg] http://apt.llvm.org/jammy/ llvm-toolchain-jammy-18 main" \
      > /etc/apt/sources.list.d/llvm.list && \
    apt-get update

# 6. Install Clang 18, Python 3, the official Python bindings for Clang 18, lcov, and graphviz for CFG visualization
RUN apt-get update && apt-get install -y \
    gcc \
    make \
    clang-18 libclang-18-dev \
    python3 python3-pip \
    python3-clang-18 \
    libx11-dev \
    lcov \
    graphviz

# 7. Install Python packages
RUN pip3 install --no-cache-dir \
    tqdm \
    openai \
    python-dotenv \
    numpy \
    pydantic \
    tree-sitter==0.23.2 \
    tree-sitter-c==0.23.2 \
    tree-sitter-languages==1.10.2 \
    faiss-cpu \
    tiktoken==0.12.0 \
    graphviz==0.20.3 \
    networkx==3.4.2 \
    google-generativeai

# 8. Clean up apt cache to reduce image size
RUN rm -rf /var/lib/apt/lists/*
