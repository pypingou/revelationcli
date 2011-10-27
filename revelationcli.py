#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
A simple command line interface for the revelation password manager.


Copyright (c) 2011 Pierre-Yves Chibon <pingou AT pingoured DOT fr>

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
import ConfigParser
import getpass
import logging
import sys
import os

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

class RevelationCli():
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

    def __browse_entry(self, itera, lvl=None, folder_only=False):
        """ For a given iterator (position) in the EntryStore, iterates
        through all the elements.
        :arg itera, an iterator (GtkTreeIter) for the EntryStore.
        :kwarg lvl, an int of the Level of the tree we are in.
        :kwarg folder_only, a boolean specifying whether the output
        should contain only the folder or not.
        """
        while self.passwords.iter_next(itera):
            self.__see_entry(itera, lvl=lvl, folder_only=folder_only)
            itera = self.passwords.iter_next(itera)
        self.__see_entry(itera, lvl=lvl, folder_only=folder_only)

    def __see_entry(self, itera, lvl=None, folder_only=False):
        """ For a given iterator (position) in the EntryStore, see if the
        corresponding entry fits our search password.
        If the entry is a folder, browse it too.
        :arg itera, an iterator (GtkTreeIter) for the EntryStore.
        :kwarg lvl, an int of the Level of the tree we are in.
        :kwarg folder_only, a boolean specifying whether the output
        should contain only the folder or not.
        """
        entry = self.passwords.get_value(itera, 2)
        LOG.debug('Entry (%s) : %s', entry.typename, entry.name)
        if lvl:
            LOG.debug('Level : %s', lvl)
            LOG.debug('Folder_only : %s', folder_only)
            if folder_only and entry.typename == 'Folder':
                print '  | ' * lvl + '\_', entry.name
            elif not folder_only:
                print '  | ' * lvl + '\_', entry.name
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
            if lvl:
                self.__browse_entry(children, lvl=lvl + 1,
                    folder_only=folder_only)
            else:
                self.__browse_entry(children, folder_only=folder_only)

    def main(self):
        """ Main function, reads the command line argument and set the
        variables accordingly
        """
        args = get_arguments()
        if args.database:
            self.dbfile = args.database
        elif self.conf.config:
            self.dbfile = os.path.expanduser(
                self.conf.config.get('revelationcli', 'database'))
        self.password_name = args.password_name
        self.show = args.show

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

    def show_tree(self, folder_only=False):
        """ Prints the revelation database as an ascii-tree into the
        terminal.
        :kwarg folder_only, a boolean specifying whether the output
        should contain only the folder or not.
        """
        LOG.debug('Show the ascii-tree of the database.')
        itera = self.passwords.get_iter_first()
        print "Database:"
        self.__browse_entry(itera, lvl=1, folder_only=folder_only)


if __name__ == "__main__":
    RevelationCli().main()
