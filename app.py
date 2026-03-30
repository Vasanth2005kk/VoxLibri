import argparse, socket, multiprocessing, sys, warnings
import os

from lib import (
    # from conf.py
    min_python_version, max_python_version, interface_port, interface_host, NATIVE,
    # from helper.py
    install_info
)


warnings.filterwarnings('ignore', category=SyntaxWarning)
warnings.filterwarnings('ignore', category=UserWarning)

def init_multiprocessing():
    try:
        multiprocessing.set_start_method('spawn')
    except RuntimeError:
        pass

def check_virtual_env()->bool:
    current_version = (sys.version_info.major, sys.version_info.minor)  # (major, minor)
    search_python_env = str(os.path.basename(sys.prefix))
    if search_python_env == 'python_env' or current_version >= min_python_version and current_version <= max_python_version:
        return True
    error=f'''***********
        Wrong launch! VoxLibrik must run in its own virtual environment!
        If the directory python_env does not exist in the VoxLibrik root directory,
        run your command with "./build.py" to install it all automatically.
        {install_info}
        ***********'''
    print(error)
    return False

def check_python_version()->bool:
    current_version = (sys.version_info.major, sys.version_info.minor)  # (major, minor)
    if current_version < min_python_version or current_version > max_python_version:
        error = f'''***********
        Wrong launch: Your OS Python version is not compatible! (current: {current_version[0]}.{current_version[1]})
        In order to install and/or use VoxLibrik correctly you must delete completely the folder python_env
        and run "./build.py".
        {install_info}
        ***********'''
        print(error)
        return False
    else:
        return True

def is_port_in_use(port:int)->bool:
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
        return s.connect_ex(('0.0.0.0',port))==0

def main()->None:
    # Argument parser to handle optional parameters with descriptions
    parser = argparse.ArgumentParser(
        description='Convert eBooks to Audiobooks using a Text-to-Speech model. Launch the GUI interface.',
        epilog=f'''
            Example usage:    
            Linux natvie mode:
                Streamlit GUI:
                ./build.py
        ''',
        formatter_class=argparse.RawTextHelpFormatter
    )
    options = [
        '--script_mode', '--help'
    ]
    
    gui_group = parser.add_argument_group('**** The following options are for gui mode only', 'Optional')
    gui_group.add_argument(options[0], type=str, help=argparse.SUPPRESS)
    
    for arg in sys.argv:
        if arg.startswith('--') and arg not in options:
            error = f'Error: Unrecognized option "{arg}"'
            print(error)
            sys.exit(1)

    args = vars(parser.parse_args())
    print(f"---> Arguments Test: {args}")
    if not 'help' in args:
        if not check_virtual_env():
            sys.exit(1)

        if not check_python_version():
            sys.exit(1)

        # Check if the port is already in use to prevent multiple launches
        if is_port_in_use(interface_port):
            error = f'Error: Port {interface_port} is already in use. The web interface may already be running.'
            print(error)
            sys.exit(1)

        args['script_mode'] = args.get('script_mode') if args.get('script_mode') else NATIVE
        
        if args['script_mode'] in [NATIVE]:
            from lib.classes.device_installer import DeviceInstaller
            manager = DeviceInstaller()
            result = manager.install_python_packages()
            if result == 0:
                device_info_str = manager.check_device_info(args['script_mode'])
                if manager.install_device_packages(device_info_str) == 1:
                    error = f'Error: Could not install device packages!'
                    print(error)
                    sys.exit(1)
        try:
            import subprocess
            from pathlib import Path as _Path
            ui_file = _Path(__file__).parent / 'lib' / 'streamlit_ui.py'
            cmd = [
                sys.executable, '-m', 'streamlit', 'run', str(ui_file),
                '--server.address',  interface_host,
                '--server.port',     str(interface_port),
                '--server.headless', 'true',
                '--server.enableCORS', 'false',
                '--browser.gatherUsageStats', 'false',
                '--theme.base',          'dark',
                '--theme.primaryColor',  '#ff8c00',
                '--theme.backgroundColor',          '#0e1117',
                '--theme.secondaryBackgroundColor',  '#1a1d27',
                '--theme.textColor',     '#e0e4f0',
                
            ]
            print(f'Starting Streamlit UI at http://{interface_host}:{interface_port}')
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print('Server interrupted by user. Shutting down...')
        except Exception as e:
            print(f'An unexpected error occurred: {e}')

if __name__ == '__main__':
    init_multiprocessing()
    main()