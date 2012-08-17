# -*- coding: utf-8 -*-
"""
/***************************************************************************
 gazetteerSearch
                                 A QGIS plugin
 Gazetteer Search plugin
                              -------------------
        begin                : 2012-07-21
        copyright            : (C) 2012 by Nathan Woodrow
        email                : woodrow.nathan@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import (QFileInfo, QSettings, QTranslator, 
                          QCoreApplication, Qt, QSizeF)
from PyQt4.QtGui import QDockWidget, QIcon, QAction, QTextDocument, QColor
from gazetteersearchdialog import gazetteerSearchDialog
from qgis.core import (QgsApplication, QgsMessageLog, QgsCoordinateReferenceSystem,
                       QgsRectangle, QgsCoordinateTransform)
from qgis.gui import QgsTextAnnotationItem

from importlib import import_module
from gazetteers import common
import resources_rc

log = lambda m: QgsMessageLog.logMessage(m,'Gazetteer')

class gazetteerSearch:
    def __init__(self, iface):
        self.dock = None
        self.results = []
        # Save reference to the QGIS interface
        self.iface = iface
        self.marker = QgsTextAnnotationItem(self.iface.mapCanvas())
        self.marker.setMapPositionFixed(True)
        self.marker.setFrameSize(QSizeF(200, 100))
        self.marker.setFrameBackgroundColor(QColor(255,219,110,150))
        self.marker.setFrameColor(QColor(255, 218,84,250))
        self.marker.setFrameBorderWidth(2)
        self.marker.hide()
        
        # Create the dialog and keep reference
        self.widget = gazetteerSearchDialog()
        self.widget.runSearch.connect(self.runSearch)
        self.widget.zoomRequested.connect(self.zoomTo)
        # initialize plugin directory
        self.plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/gazetteersearch"
        # initialize locale
        localePath = ""
        locale = QSettings().value("locale/userLocale").toString()[0:2]
       
        if QFileInfo(self.plugin_dir).exists():
            localePath = self.plugin_dir + "/i18n/gazetteersearch_" + locale + ".qm"

        if QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
   

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(QIcon(":/plugins/gazetteersearch/icon.png"), \
            u"Gazetteer Search", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&Gazetteer Search", self.action)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&Gazetteer Search",self.action)
        self.iface.removeToolBarIcon(self.action)

    # run method that performs all the real work
    def run(self):
        if not self.dock:
            self.dock = QDockWidget("Gazetteer Search", self.iface.mainWindow())
            self.dock.setWidget(self.widget)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
            self.gazetteers = common.getGazetteers()
            for gazetter in self.gazetteers.iterkeys(): 
                self.widget.addGazetter(gazetter)
        else:
            self.dock.show()
            
    def runSearch(self, searchString, selectedGazetteer):
        self.widget.clearResults()
        gazetteer_config = self.gazetteers[str(selectedGazetteer)]
        gazetteer = self.getGazetteerModule(gazetteer_config)
        params = common.perpareParams(gazetteer.params, searchString)
        log(params)
        log(gazetteer.url)
        data = common.search(gazetteer.url, params)
        self.results = list(gazetteer.parseRequestResults(data))
        for res in self.results:
            self.widget.addResult(res.description)
            
    def getGazetteerModule(self, config):
        gazetteer_module = config['gazetteer']    
        imported_gazetteer = import_module('gazetteersearch.gazetteers.%s' % gazetteer_module)
        return imported_gazetteer
            
    def zoomTo(self, name):
        for res in self.results:
            if res.description == name:
                dest_crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
                src_crs = QgsCoordinateReferenceSystem()
                src_crs.createFromEpsg(27700)
                transform = QgsCoordinateTransform(src_crs, dest_crs)
                new_point = transform.transform(res.x, res.y)
                x = new_point.x()
                y = new_point.y()
                self.iface.mapCanvas().setExtent(QgsRectangle(x,y,x,y))
                self.iface.mapCanvas().zoomScale(res.zoom)
                self.iface.mapCanvas().refresh()
                self.marker.setMapPosition(new_point)
                doc = QTextDocument()
                doc.setHtml('<p align=center>%s</p>' % res.description)
                self.marker.setDocument(doc)
                self.marker.show()
                return
            
