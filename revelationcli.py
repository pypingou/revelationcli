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
import getpass
import logging
import sys

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
    parser.add_argument('database', help='The revelation database to \
        open')
    parser.add_argument('password_name', nargs='?', default=None,
        help='Name of the password to retrieve from the revelation \
        database.')
    parser.add_argument('--show', action='store_true',
        help='Actually prints the password to the terminal')
    parser.add_argument('--showtree', action='store_true',
        help='Actually prints the tree of passwords and folder in the \
        terminal.')
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

    def __browse_entry(self, itera, lvl=None):
        """ For a given iterator (position) in the EntryStore, iterates
        through all the elements.
        :arg itera, an iterator (GtkTreeIter) for the EntryStore.
        :arg lvl, an int of the Level of the tree we are in.
        """
        while self.passwords.iter_next(itera):
            self.__see_entry(itera, lvl=lvl)
            itera = self.passwords.iter_next(itera)
        self.__see_entry(itera, lvl=lvl)

    def __see_entry(self, itera, lvl=None):
        """ For a given iterator (position) in the EntryStore, see if the
        corresponding entry fits our search password.
        If the entry is a folder, browse it too.
        :arg itera, an iterator (GtkTreeIter) for the EntryStore.
        :arg lvl, an int of the Level of the tree we are in.
        """
        entry = self.passwords.get_value(itera, 2)
        LOG.debug("Entry (%s) : %s", entry.typename, entry.name)
        if lvl:
            LOG.debug("Level : %s", lvl)
            print "  | " * lvl + "\_", entry.name
        elif entry.name == self.password_name:
            print "  Name :", entry.name
            for field in entry.fields:
                if field.value != "":
                    if field.name != "Password":
                        print "  %s : %s" % (field.name, field.value)
                    elif self.show:
                        print "  %s : %s" % (field.name, field.value)
        if self.passwords.iter_has_child(itera):
            children = self.passwords.iter_children(itera)
            if lvl:
                self.__browse_entry(children, lvl=lvl + 1)
            else:
                self.__browse_entry(children)

    def main(self):
        """ Main function, reads the command line argument and set the
        variables accordingly
        """
        args = get_arguments()
        self.dbfile = args.database
        self.password_name = args.password_name
        self.show = args.show

        self.dbdata = read_file(self.dbfile)
        self.passwords = self.read_revelation_file()
        if args.showtree:
            self.show = False
            self.show_tree()
        else:
            self.get_password()

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

    def show_tree(self):
        """ Prints the revelation database as an ascii-tree into the
        terminal.
        """
        LOG.debug('Show the ascii-tree of the database.')
        itera = self.passwords.get_iter_first()
        print "Database:"
        self.__browse_entry(itera, 1)


if __name__ == "__main__":
    RevelationCli().main()
