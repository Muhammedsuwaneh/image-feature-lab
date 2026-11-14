import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: mainWindow
    required property var viewModel
    width: 1440
    height: 920
    minimumWidth: 1120
    minimumHeight: 720
    visible: true
    title: qsTr("FeatureLab | Distance Concentration")
    color: theme.canvas

    QtObject {
        id: theme
        readonly property color canvas: "#F1F3EE"
        readonly property color surface: "#FFFFFF"
        readonly property color ink: "#182722"
        readonly property color muted: "#6E7B74"
        readonly property color line: "#DCE2DA"
        readonly property color rail: "#172A25"
        readonly property color railMuted: "#A8B9B0"
        readonly property color accent: "#C75D43"
        readonly property color accentSoft: "#F8EDE8"
        readonly property color green: "#537461"
        readonly property color paleGreen: "#EAF0EA"
    }

    property var pageSources: ({
        "Dashboard": "pages/Dashboard.qml",
        "ImageAnalysis": "pages/ImageAnalysis.qml",
        "DistanceConcentration": "pages/DistanceConcentration.qml",
        "DimensionalityExperiments": "pages/DimensionalityExperiments.qml",
        "Results": "pages/Results.qml"
    })

    function loadCurrentPage() {
        pageLoader.setSource(pageSources[viewModel.currentPage], {"viewModel": viewModel, "theme": theme})
    }

    Component.onCompleted: loadCurrentPage()
    Connections {
        target: mainWindow.viewModel
        function onCurrentPageChanged() { mainWindow.loadCurrentPage() }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Sidebar {
            Layout.fillHeight: true
            Layout.preferredWidth: 252
            Layout.minimumWidth: 252
            viewModel: mainWindow.viewModel
            theme: theme
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 82
                color: theme.surface
                border.color: theme.line
                border.width: 0

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 34
                    anchors.rightMargin: 34
                    spacing: 20

                    ColumnLayout {
                        spacing: 4
                        Text {
                            text: "FEATURELAB  /  RESEARCH CONSOLE"
                            color: theme.green
                            font.family: "Bahnschrift"
                            font.pixelSize: 10
                            font.weight: Font.Bold
                        }
                        Text {
                            text: mainWindow.viewModel.currentPageTitle
                            color: theme.ink
                            font.family: "Bahnschrift"
                            font.pixelSize: 22
                            font.weight: Font.DemiBold
                        }
                    }

                    Item { Layout.fillWidth: true }

                    Rectangle {
                        Layout.preferredWidth: 218
                        Layout.preferredHeight: 32
                        radius: 4
                        color: theme.canvas
                        border.color: theme.line

                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 8
                            Rectangle {
                                Layout.preferredWidth: 7
                                Layout.preferredHeight: 7
                                radius: 3.5
                                color: theme.accent
                            }
                            Text {
                                  text: mainWindow.viewModel.datasetLoading
                                      ? "LOADING DIGITS DATASET..."
                                      : mainWindow.viewModel.hasDigitsDataset
                                      ? "DIGITS BASELINE / " + mainWindow.viewModel.datasetSampleCount + " SAMPLES"
                                      : "DIGITS DATASET UNAVAILABLE"
                                color: theme.muted
                                font.family: "Bahnschrift"
                                font.pixelSize: 9
                                font.weight: Font.Bold
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: datasetStateRow.implicitHeight + 20
                visible: !mainWindow.viewModel.hasDigitsDataset || mainWindow.viewModel.knnEvaluationError.length > 0
                color: theme.accentSoft
                RowLayout {
                    id: datasetStateRow
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.margins: 20
                    spacing: 12
                    Text {
                        objectName: "datasetStatusText"
                        Layout.fillWidth: true
                        text: mainWindow.viewModel.datasetLoading ? "Initializing scikit-learn Digits..."
                            : mainWindow.viewModel.datasetError ? "Dataset loading failed: " + mainWindow.viewModel.datasetError
                            : mainWindow.viewModel.knnEvaluationError ? "Dataset ready. Baseline evaluation failed: " + mainWindow.viewModel.knnEvaluationError + ". Experiments remain available."
                            : "Initialize scikit-learn Digits to start analysis and experiments."
                        color: theme.ink
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }
                    Button {
                        objectName: "loadDatasetButton"
                        visible: !mainWindow.viewModel.hasDigitsDataset
                        text: mainWindow.viewModel.datasetLoading ? "Loading..."
                            : mainWindow.viewModel.datasetError ? "Retry dataset loading" : "Load Digits dataset"
                        enabled: !mainWindow.viewModel.datasetLoading
                        onClicked: mainWindow.viewModel.initializeDataset()
                    }
                    Button {
                        visible: mainWindow.viewModel.hasDigitsDataset && mainWindow.viewModel.knnEvaluationError.length > 0
                        text: "Retry baseline evaluation"
                        enabled: !mainWindow.viewModel.knnEvaluationRunning
                        onClicked: mainWindow.viewModel.evaluateKnnClassifier()
                    }
                }
            }

            Loader {
                id: pageLoader
                objectName: "pageLoader"
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }
    }
}
