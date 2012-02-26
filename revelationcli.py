#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
A simple command line interface for the revelation password manager.


Copyright (c) 2011-2012 Pierre-Yves Chibon <pingou AT pingoured DOT fr>

This file is part of revelationcli.

revelationcli is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

revelationcli is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with revelationcli.  If not, see <http://www.gnu.org/licenses/>.
"""

from revelation.datahandler import detect_handler
from revelation.io import DataFile

import argparse
import cmd
import ConfigParser
import getpass
import logging
import sys
import os

TKIMPORT = True
try:
    from Tkinter import Tk
except ImportError:
    TKIMPORT = False

# Initial simple logging stuff
logging.basicConfig()
LOG = logging.getLogger('revelationcli')
if '--debug' in sys.argv:
    LOG.setLevel(logging.DEBUG)
elif '--verbose' in sys.argv:
    LOG.setLevel(logging.INFO)


def get_arguments():
    """ Handle the command line arguments given to this program """
    LOG.debug('Parse command line argument')
    parser = argparse.ArgumentParser(description='Command line client \
        for revelation, the password manager.')
    parser.add_argument('database', nargs='?', default=None,
        help='The revelation database to open')
    parser.add_argument('-i', '--interactive',
                        help='Enter PyPass interactive mode',
                        action='store_true', default=False)
    parser.add_argument('password_name', nargs='?', default=None,
        help='Name of the password to retrieve from the revelation \
        database.')
    parser.add_argument('--show', action='store_true',
        help='Actually prints the password to the terminal')
    parser.add_argument('--show-tree', action='store_true',
        dest="show_tree",
        help='Prints the tree of passwords and folder in the \
        terminal.')
    parser.add_argument('--show-folders', action='store_true',
        dest="show_folders",
        help='Prints the tree of folders in the terminal.')
    parser.add_argument('--verbose', action='store_true',
                help="Gives more info about what's going on")
    parser.add_argument('--debug', action='store_true',
                help="Outputs bunches of debugging info")
    return parser.parse_args()


def read_file(dbfile):
    """ Open a give file and returns its content.
    :arg dbfile, the file to open and read
    """
    LOG.debug('Open revelation database: %s', dbfile)
    flux = open(dbfile)
    data = flux.read()
    flux.close()
    return data


class Config(object):
    """ A config class to load/handle configuration file of revelationcli.
    """
    
    def __init__(self):
        """ Default constructor, loads the configuration file if present
        and keeps the configuration accessible.
        """
        if os.path.exists(os.path.expanduser("~/.config/revelationcli")):
            self.config = ConfigParser.ConfigParser()
            self.config.read(os.path.expanduser("~/.config/revelationcli"))
        else:
            self.config = None

    def exists(self):
        """ Returns a boolean whether the configuration file exists and
        has been loaded or not.
        """
        if self.config:
            return True
        else:
            return False

    def get(self, section, option):
        """ Retrieve an specific option in a defined section of the
        configuration file
        :arg section, the name of the section to look into (section are
        marker [section name])
        :arg option, the name of the option to search for in the given
        section
        """
        return self.config.get(section, option)

class RevelationCli(object):
    """ RecelationCli class, handling the element needed to search for
    passwords in a revelation database.
    """

    def __init__(self):
        self.show = False
        self.list_element = False
        self.password_name = None
        self.dbfile = None
        self.dbdata = None
        self.passwords = None
        self.conf = Config()

    def _browse_entry(self, itera, lvl=None, folder_only=False,
        iterative=True):
        """ For a given iterator (position) in the EntryStore, iterates
        through all the elements.
        :arg itera, an iterator (GtkTreeIter) for the EntryStore.
        :kwarg lvl, an int of the Level of the tree we are in.
        :kwarg folder_only, a boolean specifying whether the output
        should contain only the folder or not.
        :kwarg iterative, boolean to iterate over the whole tree or not.
        """
        while self.passwords.iter_next(itera):
            self._see_entry(itera, lvl=lvl, folder_only=folder_only,
                iterative=iterative)
            itera = self.passwords.iter_next(itera)
        self._see_entry(itera, lvl=lvl, folder_only=folder_only,
            iterative=iterative)

    def _see_entry(self, itera, lvl=None, folder_only=False,
        iterative=True):
        """ For a given iterator (position) in the EntryStore, see if the
        corresponding entry fits our search password.
        If the entry is a folder, browse it too.
        :arg itera, an iterator (GtkTreeIter) for the EntryStore.
        :kwarg lvl, an int of the Level of the tree we are in.
        :kwarg folder_only, a boolean specifying whether the output
        should contain only the folder or not.
        :kwarg iterative, boolean to iterate over the whole tree or not.
        """
        entry = self.passwords.get_value(itera, 2)
        LOG.debug('Entry (%s) : %s', entry.typename, entry.name)
        if lvl:
            LOG.debug('Level : %s', lvl)
            LOG.debug('Folder_only : %s', folder_only)
            if folder_only and entry.typename == 'Folder':
                print '  | ' * lvl + '\_ []', entry.name
            elif not folder_only:
                if entry.typename == 'Folder':
                    print '  | ' * lvl + '\_ []', entry.name
                else:
                    print '  | ' * lvl + '\_ ', entry.name
        elif entry.name == self.password_name:
            print '  Name :', entry.name
            for field in entry.fields:
                if field.value != "":
                    if field.name != 'Password':
                        print '  %s : %s' % (field.name, field.value)
                    elif self.show:
                        print '  %s : %s' % (field.name, field.value)
        if self.passwords.iter_has_child(itera):
            children = self.passwords.iter_children(itera)
            if lvl and iterative:
                self._browse_entry(children, lvl=lvl + 1,
                    folder_only=folder_only)
            elif iterative:
                self._browse_entry(children, folder_only=folder_only)

    def main(self):
        """ Main function, reads the command line argument and set the
        variables accordingly
        """
        args = get_arguments()
        if args.database:
            self.dbfile = args.database
        elif self.conf.exists():
            self.dbfile = os.path.expanduser(
                self.conf.get('revelationcli', 'database'))
        self.password_name = args.password_name
        self.show = args.show

        if not self.dbfile:
            print "No database file specified"
            sys.exit(3)
        try:
            self.dbdata = read_file(self.dbfile)
            self.passwords = self.read_revelation_file()
        except IOError, exc:
            LOG.debug(exc)
            print "File could not be found or read"
            sys.exit(1)
        except Exception, exc:
            LOG.debug(exc)
            print "Wrong password entered"
            sys.exit(2)

        if args.interactive:
            try:
                ppi = RevelationInteractive(self.passwords)
                ppi.cmdloop()
            except KeyboardInterrupt:
                ppi.do_quit(None)
                print ""

        if args.show_folders:
            self.show = False
            self.show_tree(folder_only=True)
        else:
            self.show_tree()

    def get_password(self):
        """ Retrieve the root element of the tree and start browsing the
        tree for the searched password.
        """
        LOG.debug('Browse passwords to find the one requested.')
        itera = self.passwords.get_iter_first()
        self.__browse_entry(itera)

    def read_revelation_file(self):
        """ Decrypt the content of the revelation database.
        """
        LOG.debug('Read the content of the database.')
        handler = detect_handler(self.dbdata)
        dafi = DataFile(handler)
        password = getpass.getpass()
        content = dafi.load(self.dbfile, password=password)
        return content

    def show_tree(self, folder_only=False, iterative=True):
        """ Prints the revelation database as an ascii-tree into the
        terminal.
        :kwarg folder_only, a boolean specifying whether the output
        should contain only the folder or not.
        """
        LOG.debug('Show the ascii-tree of the database.')
        itera = self.passwords.get_iter_first()
        print "Database:"
        self._browse_entry(itera, lvl=1, folder_only=folder_only,
            iterative=iterative)


class RevelationInteractive(cmd.Cmd, RevelationCli):

    def __init__(self, passwords, filename=None):
        cmd.Cmd.__init__(self)
        self.passwords = passwords
        self.intro = 'See `help` for a list of the command available.'
        self.path = "/"
        self.modified = False
        self.itera = self.passwords.get_iter_first()
        self.root_itera = self.passwords.get_iter_first()
        if not TKIMPORT:
            warn('The copy command from the interactive shell will not be available. '\
        'Install the Tkinter library to have it.')

    def complete_cat(self, text, line, start_index, end_index):
        options = [account.name for account in self.folder.accounts]
        return options

    def complete_cd(self, text, line, start_index, end_index):
        options = [folder.name for folder in self.folder.folders]
        return options

    def complete_cmd(self, text, line, start_index, end_index):
        commands = ['add', 'add_folder', 'cat', 'cd', 'exit', 'ls', 'pwd',
            'quit', 'remove', 'save', 'view']
        return commands
    
    def complete_view(self, text, line, start_index, end_index):
        options = [account.name for account in self.folder.accounts]
        return options

    def do_add(self, params):
        """ Add a password in the database. """
        print 'Adding a password into the folder: %s' % self.path
        name = params
        if not name:
            name = raw_input('Name: ')
        password = getpass.getpass('Password: ')
        account = PypAccount(name, password)
        add_extras = raw_input( 'Do you want to add extra-information? [Y/N] ')
        while add_extras.lower().startswith('y'):
            key = raw_input('Title: ')
            value = raw_input('Value: ')
            account.extras[key] = value
            add_extras = raw_input( 'Do you want to add extra-information? [Y/N] ')
        self.folder.accounts.append(account)
        self.modified = True

    def do_add_folder(self, params):
        """ Add a folder in the current directory. """
        name = params
        if not name:
            name = raw_input('Name: ')
        desc = raw_input('Description: ')
        folder = PypFolder(name, desc)
        self.folder.folders.append(folder)
        self.modified = True

    def do_cat(self, params):
        """ Display the information relative to a given password. """
        self.do_view(params)

    def do_cd(self, params):
        """ Change the working directory. """
        if not params:
            self.itera = self.root_itera
            self.path = '/'
            return

        #if params == '..':
            #path = self.path.split('/')
            #self.folder = self.pyp_main_folder
            #self.path = '/'
            #for folder in path[1:-2]:
                #self.do_cd(folder)
            #return

        found = False
        itera = self.itera
        while self.passwords.iter_next(itera):
            entry = self.passwords.get_value(itera, 2)
            LOG.debug('- Entry (%s) : %s', entry.typename, entry.name)
            if entry.name == params:
                self.itera = itera
                found = True
                break
            itera = self.passwords.iter_next(itera)
        entry = self.passwords.get_value(itera, 2)
        LOG.debug('* Entry (%s) : %s', entry.typename, entry.name)
        if entry.name == params:
                self.itera = itera
                found = True
        
        if not found:
            print 'No folder of the name "%s" were found in this folder.' % params

    def do_copy(self, params):
        """ Copy the password of the given account to the clipboard. """
        if not TKIMPORT:
            print 'Command not available.'
            return
        if not params:
            print 'No password specified'
        else:
            found = False
            for account in self.folder.accounts:
                if account.name == params:
                    r = Tk()
                    r.withdraw()
                    r.clipboard_clear()
                    r.clipboard_append(account.password)
                    print 'Password for the account %s copied to clipboard' % account.name
                    found = True
            if not found:
                print 'No password of the name "%s" were found in this folder.' % params

    def do_exit(self, params):
        """ Quit the program. """
        self.do_quit(params)

    def do_ls(self, params):
        """ List directory and password available in the current
        directory.
        """
        if not params:
            print self.itera
            self._browse_entry(self.itera, lvl=1, folder_only=False,
            iterative=False)
        else:
            print params
            
            found = False
            itera = self.itera
            while self.passwords.iter_next(itera):
                entry = self.passwords.get_value(itera, 2)
                LOG.debug('- Entry (%s) : %s', entry.typename, entry.name)
                if entry.name == params:
                    self.itera = itera
                    found = True
                    break
                itera = self.passwords.iter_next(itera)
            entry = self.passwords.get_value(itera, 2)
            LOG.debug('* Entry (%s) : %s', entry.typename, entry.name)
            if entry.name == params:
                    self.itera = itera
                    found = True
            
            entry = self.passwords.get_value(self.itera, 2)
            LOG.debug('Entry (%s) : %s', entry.typename, entry.name)
            if self.passwords.iter_has_child(self.itera):
                children = self.passwords.iter_children(self.itera)
                self._browse_entry(children, lvl=1,
                        folder_only=False, iterative=False)

    def do_pwd(self, params):
        """ Print the working directory. """
        print self.path

    def do_quit(self, params):
        """ Quit the program. """
        if self.modified:
            print 'The database has been modified.'
            usr_inp = raw_input('Do you want to quit (q), save (s), cancel (c)? ')
            if usr_inp.lower() == 'c':
                return
            elif usr_inp.lower() == 's':
                self.do_save(None)
        sys.exit(1)

    def do_remove(self, params):
        """ Remove a password from the database.
        """
        if not params:
            print 'Please specify the password or folder to remove.'
        else:
            for folder in self.folder.folders:
                if params == folder.name:
                    usr_inp = raw_input('Are you sure you want to remove the folder "%s"? [Y/N] ' %
                        params)
                    if usr_inp.lower().startswith('y'):
                        self.folder.folders.remove(folder)
                        self.modified = True
            for account in self.folder.accounts:
                if params == account.name:
                    usr_inp = raw_input('Are you sure you want to remove the account "%s"? [Y/N] ' %
                        params)
                    if usr_inp.lower().startswith('y'):
                        self.folder.accounts.remove(account)
                        self.modified = True

    def do_save(self, params):
        """ Save the current database.
    :arg filename to which the database will be saved, if not specified
        it will save the current file or will take it the default from
        the configuration file."""
        self.pyp.data = self.pyp_main_folder.dump()
        if not params and not self.filename:
            print 'Please specify a filename to which save the database.'
        elif self.filename and not params:
            outcome = self.pyp.crypt(filename = self.filename, force=True)
            if outcome is False:
                print 'Could not save the database, Wrong/Expired key?'
            elif outcome == 'key_not_found':
                print 'No key specified in the configuration file.'
            elif outcome == 'file_exists':
                print 'This database file already exists.'
            else:
                self.modified = False
        elif params:
            outcome = self.pyp.crypt(filename = params)
            if outcome is False:
                print 'Could not save the database, Wrong/Expired key?'
            elif outcome == 'key_not_found':
                print 'No key specified in the configuration file.'
            elif outcome == 'file_exists':
                print 'This database file already exists.'
                usr_inp = raw_input( 'To you want to over write this file? [Y/N]')
                if usr_inp.lower().startswith('y'):
                    self.pyp.crypt(filename = params, force=True)
                    self.modified = False
            else:
                self.modified = False

    def do_view(self, params):
        """ Display the information relative to a given password. """
        if not params:
            print 'No password specified'
        else:
            found = False
            for account in self.folder.accounts:
                if account.name == params:
                    print account
                    found = True
            if not found:
                print 'No password of the name "%s" were found in this folder.' % params

    def view_folder(self, folder):
        """ Display the content of a folder. """
        if len(folder.folders) > 0:
            print _("Folders:")
            for fold in folder.folders:
                print "  " + fold.name

        if len(folder.accounts) > 0:
            print _("Accounts:")
            for account in folder.accounts:
                print '  %s' % account.name


if __name__ == "__main__":
    RevelationCli().main()
