from os.path import dirname
from sys import exit

from PyQt6.QtCore import QRect
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton, QApplication, QLabel, QLineEdit, QSpinBox, QMessageBox, \
    QProgressBar


class App(QWidget):
    URL = ''

    def __init__(self):
        super().__init__()
        self.setGeometry(QRect(100, 100, 350, 200))
        self.initUI()
        self.setStatusTip('Ready')

    def initUI(self):
        self.setWindowIcon(QIcon(dirname(__file__) + '\\icon.ico'))
        self.setWindowTitle('Thread Downloader')

        grid = QGridLayout()

        labURL = QLabel('URL')
        grid.addWidget(labURL, 0, 0)

        self.leURL = QLineEdit()
        self.leURL.setToolTip('The URL of the file you want to download.')
        grid.addWidget(self.leURL, 0, 1)

        labThreadCount = QLabel('Thread count')
        grid.addWidget(labThreadCount, 1, 0)

        self.sbThreadCount = QSpinBox()
        self.sbThreadCount.setToolTip('Thread count')
        self.sbThreadCount.setMinimum(1)
        grid.addWidget(self.sbThreadCount, 1, 1)

        self.ps = QPushButton('Start')
        self.ps.clicked.connect(self.start)
        grid.addWidget(self.ps, 2, 0)

        labPbDL = QLabel('Download')
        grid.addWidget(labPbDL, 3, 0)

        self.pbDL = QProgressBar()
        grid.addWidget(self.pbDL, 3, 1, 2, 1)

        labPbWT = QLabel('Write')
        grid.addWidget(labPbWT, 4, 0)

        self.pbWT = QProgressBar()
        grid.addWidget(self.pbWT, 4, 1, 2, 1)

        self.setLayout(grid)

        self.show()

    def start(self):
        if not self.URL:
            QMessageBox.warning(self, 'Oops', 'URL cannot be empty.')
            return
        # self.leURL.setReadOnly(True)
        # self.sbThreadCount.setReadOnly(True)


app = QApplication([])
window = App()
window.show()
exit(app.exec())
