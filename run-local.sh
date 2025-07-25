echo "Building frontend..."
cd frontend && \
npm install -g gatsby-cli && \
npm install -g yarn && \
yarn install && \
yarn build && \

echo "Installing backend..."
cd .. && \
uv pip install -e . && \

echo "Running backend..."
magentic-ui --config config.yaml