apt install rsync git nodejs npm -y

echo "Building frontend..."
cd frontend && \
npm install -g gatsby-cli && \
npm install -g yarn && \
apt-get install libvips libvips-dev libvips-tools && \
yarn config set registry https://registry.npmmirror.com --global && \
yarn config set sharp_binary_host "https://registry.npmmirror.com/sharp" && \
yarn config set sharp_libvips_binary_host "https://registry.npmmirror.com/sharp-libvips" && \
yarn install && \
yarn build

echo "Creating conda environment..."
conda create -n magentic-ui python=3.12 -y && conda activate magentic-ui

echo "Installing backend..."
cd .. && \
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
pip install -e .

echo "Running backend..."
magentic-ui --config config.yaml --host 0.0.0.0 --port 8000

