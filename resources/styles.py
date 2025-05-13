from PyQt5.QtWidgets import QLabel

class Styles:
    upload_button_styling =  """
            QPushButton {
                border: 2px solid #a9cfbd;  /* Set border color and width */
                border-radius: 10px;        /* Set border radius for rounded corners */
                padding: 10px;              /* Add padding inside the label */
                background-color: #808080;  /* Set background color to grey */
                font-size: 12px;            /* Set font size */
                color: white;               /* Set font color */
                max-width: 70px;            /* Set a fixed minimum width */
            }
            QPushButton:hover {
                background-color: #a9a9a9;  /* Change background color on hover */
            }
        """
    
    reset_button_styling = """
        QPushButton {
            border: 2px solid #a9cfbd;  /* Set border color and width */
            border-radius: 10px;        /* Set border radius for rounded corners */
            padding: 5px;              /* Add padding inside the label */
            background-color: #808080;  /* Set background color to grey */
            font-size: 11px;            /* Set font size */
            color: white;               /* Set font color */
            max-width: 40px;            /* Set a fixed minimum width */
        }
        QPushButton:hover {
            background-color: #a9a9a9;  /* Change background color on hover */
        }
    """

    overlay_button_styling = """
            QPushButton {
                border: 2px solid #a9cfbd;  /* Set border color and width */
                border-radius: 5px;        /* Set border radius for rounded corners */
                padding: 5px;              /* Add padding inside the label */
                background-color: #808080;  /* Set background color to grey */
                font-size: 9px;            /* Set font size */
                color: white;               /* Set font color */
                max-width: 60px;            /* Set a fixed minimum width */
            }
            QPushButton:hover {
                background-color: #a9a9a9;  /* Change background color on hover */
            }
        """
    
    runARI_button_styling = """
            QPushButton {
                border: 2px solid #a9cfbd;  /* Set border color and width */
                border-radius: 5px;        /* Set border radius for rounded corners */
                padding: 5px;              /* Add padding inside the label */
                background-color: #808080;  /* Set background color to grey */
                font-size: 9px;            /* Set font size */
                color: white;               /* Set font color */
                max-width: 60px;            /* Set a fixed minimum width */
            }
            QPushButton:hover {
                background-color: #a9a9a9;  /* Change background color on hover */
            }
        """
    
    runARI_button_styling = """
            QPushButton {
                border: 2px solid #a9cfbd;  /* Set border color and width */
                border-radius: 10px;        /* Set border radius for rounded corners */
                padding: 10px;              /* Add padding inside the label */
                background-color: #82e677;  /* Set background color to grey */
                font-size: 14px;            /* Set font size */
                color: white;               /* Set font color */
                max-width: 70px;            /* Set a fixed minimum width */
            }
            QPushButton:hover {
                background-color: #3e8237;  /* Change background color on hover */
            }
        """

    orth_view_styling = [
            "border: 2px solid #a9cfbd;",  # Set border color and width
            "border-radius: 10px;",        # Set border radius for rounded corners
            "padding: 0px;",               # Add padding inside the label
            "background-color: #091c13;"   # Set background color
            ]
    
    left_box_styling  = [
            "border: 2px solid #a9cfbd;",  # Set border color and width
            "border-radius: 10px;",        # Set border radius for rounded corners
            "padding: 0px;",               # Add padding inside the label
            "background-color: #091c13;"   # Set background color
        ]

    @staticmethod
    def orth_title_style(text, width=400, height=20):
        label = QLabel(text)
        label.setStyleSheet(
            "border: 2px solid #000000;"  # Set border color and width
            "border-radius: 10px;"        # Set border radius for rounded corners
            "padding: 5px;"               # Add padding inside the label
            "background-color: #6ca88b;"  # Set background color
        )
        label.setFixedWidth(width)  # Set the fixed height of the label
        label.setFixedHeight(height)  # Set the fixed height of the label
        return label
    
    @staticmethod
    def cluster_viewer_title_style(text, width=400, height=20):
        label = QLabel(text)
        label.setStyleSheet(
            "border: 2px solid #000000;"  # Set border color and width
            "border-radius: 10px;"        # Set border radius for rounded corners
            "padding: 5px;"               # Add padding inside the label
            "background-color: #253d32;"  # Set background color
        )
        label.setFixedWidth(width)  # Set the fixed height of the label
        label.setFixedHeight(height)  # Set the fixed height of the label
        return label
    
    plus_button_styling = """
            QPushButton {
                background-color: #3d2130;  /* Pastel green */
                color: white; 
                font-size: 20px; 
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #81c784;  /* Darker pastel green on hover */
            }
        """
    
    minus_button_styling = """
            QPushButton {
                background-color: #3d2130;  /* Pastel red */
                color: white; 
                font-size: 20px; 
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #ff6f69;  /* Darker pastel red on hover */
            }
        """
    
    reset_button2_styling = """
            QPushButton {
                background-color: #b0bec5;  /* Pastel grey */
                color: white; 
                font-size: 16px; 
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #90a4ae;  /* Darker pastel grey on hover */
            }
        """
    
    accept_button_styling = """
            QPushButton {
                background-color: #2d7037;  /* Pastel grey */
                color: white; 
                font-size: 13px; 
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #90a4ae;  /* Darker pastel grey on hover */
            }
        """
    
    work_station_table_styling = """
            QTableWidget {
                font-size: 16px;                  /* Enlarge the text */
                background-color: #2e2e2e;        /* Dark background */
                color: white;                     /* White text */
                gridline-color: #444444;           /* Subtle gridline color */
                selection-background-color: #3a9ad9;  /* Modern blue for selection */
                border-radius: 5px;               /* Rounded corners */
                padding: 5px;                     /* Padding for a clean look */
            }
            QHeaderView::section {
                background-color: #3a3a3a;        /* Darker header background */
                color: white;                     /* White header text */
                font-size: 15px;                  /* Larger text for header */
                font-weight: bold;                /* Bold header text */
                padding: 5px;                     /* Padding for a clean look */
                border: 1px solid #3a9ad9;        /* Border around headers */
            }
            QTableWidget::item {
                padding: 10px;                    /* Extra padding for cells */
                border: none;                     /* Remove default borders */
            }
            QTableWidget::item:hover {
                background-color: #3a9ad9;        /* Hover effect for items */
                color: black;                     /* Change text color on hover */
            }

        """
    
    cluster_slider_styling = """
            QSlider::groove:horizontal {
                background: #444;  /* Groove color */
                height: 6px;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background: white;  /* Handle color */
                border: 1px solid #555;
                width: 16px;
                margin: -5px 0;  /* Align handle properly */
                border-radius: 8px;
            }
            
            QSlider::tick-mark:horizontal {
                background: black;  /* Tick mark color */
                width: 2px;  /* Tick width */
                height: 10px; /* Tick height */
            }
            
            QSlider::sub-page:horizontal {
                background: #888;  /* Left side filled section */
                border-radius: 3px;
            }
        """
    
    controls_panel_styling = """
            QGroupBox {
                border: 1px solid grey;
                border-radius: 8px;
                margin-top: 10px;
                padding: 8px;
                background-color: #222222;
                color: #DDDDDD;
                font-size: 12pt;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 10px;
                font-weight: bold;
                color: #FFFFFF;
            }

            QPushButton {
                background-color: #333333;
                color: #DDDDDD;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 11pt;
            }

            QPushButton:hover {
                background-color: #555555;
                border: 1px solid #777777;
            }

            QPushButton:pressed {
                background-color: #777777;
                border: 1px solid #999999;
            }
        """