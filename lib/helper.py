from pathlib import Path

install_info = r'''
After the first run, you are free to use your command line with:
# go into Voxlibir folder then:
----------------------------------
conda activate ./python_env
python app.py [options]
conda deactivate
----------------------------------
Available command options, type:
# or if conda ./python_env activated:
python app.py --help
'''


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _prog_version() -> str:
    vfile = PROJECT_ROOT / "VERSION.txt"
    return vfile.read_text().strip() if vfile.exists() else "dev"