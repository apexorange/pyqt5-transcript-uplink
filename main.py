from gui import *

def main():
    app = QApplication(sys.argv)
    # Apply the complete dark theme to your Qt App.
    # qdarktheme.setup_theme("light")
    ex = TextProcessorApp()
    ex.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
