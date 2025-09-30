
Summary:
GUI application to run pytest tests. Should be developed using python language

Description:
This application is used by tester to run tests using GUI.

Features:
Build tree of tests, based on tests hierarchy on disk.
Mark tests that should be run using checkboxes (checkbox on each test, on folder, option to select and deselect all).
Filter tests according to the pytest markers (builtin and custom, defined in pytest.ini).
Ability to configure pytest enviroment variables (.env file options).
Ability to specify options for the pytest using checkboxes (description of of each option should be displayed too).
Display the progress bar displayinfg the current status of test run.
Buttons for the Start test run, Stop test run.

Tests located in this project in directory test\
Add simple test to test functionality