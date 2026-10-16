import sys
from pathlib import Path

# Coloca a raiz do projeto no caminho de importação para os testes enxergarem os pacotes.
sys.path.insert(0, str(Path(__file__).resolve().parent))
