import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: page
    objectName: "dimensionalityExperimentsPage"
    property var viewModel
    property var theme

    ScrollView {
        anchors.fill: parent
        clip: true
        leftPadding: 34
        rightPadding: 34
        topPadding: 30
        bottomPadding: 30
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 20

            PageHeader {
                theme: page.theme
                eyebrow: "EXPERIMENTS / DIMENSIONALITY"
                title: "Vary the feature dimension."
                description: "Set up a controlled comparison of distance geometry and nearest-neighbor behavior across feature dimensions."
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.minimumHeight: 330
                spacing: 14

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 440
                    radius: 6
                    color: page.theme.surface
                    border.color: page.theme.line

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 22
                        spacing: 16
                        Text {
                            text: "EXPERIMENT DESIGN"
                            color: page.theme.green
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.weight: Font.Bold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Comparison parameters"
                            color: page.theme.ink
                            font.family: "Bahnschrift"
                            font.pixelSize: 19
                            font.weight: Font.DemiBold
                        }

                        GridLayout {
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: 18
                            rowSpacing: 14

                            Text { text: "Feature dimensions (fixed)"; color: page.theme.ink; font.family: "Segoe UI"; font.pixelSize: 11 }
                            TextField {
                                Layout.fillWidth: true
                                text: "64, 96, 160, 256"
                                color: "#000000"
                                readOnly: true
                                selectByMouse: true
                                background: Rectangle { radius: 4; color: "#F8F9F6"; border.color: page.theme.line }
                            }
                            Text { text: "Distance metric"; color: page.theme.ink; font.family: "Segoe UI"; font.pixelSize: 11 }
                            ComboBox {
                                Layout.fillWidth: true
                                model: ["Euclidean (fixed)"]
                                enabled: false
                            }
                            Text { text: "Classifier"; color: page.theme.ink; font.family: "Segoe UI"; font.pixelSize: 11 }
                            ComboBox {
                                Layout.fillWidth: true
                                model: ["k-NN, k = 5 (fixed)"]
                                enabled: false
                            }
                        }

                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: page.theme.line }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Rectangle {
                                Layout.preferredWidth: 7
                                Layout.preferredHeight: 7
                                radius: 3.5
                                color: page.theme.accent
                            }
                            Text {
                                Layout.fillWidth: true
                                text: "Run experiment uses these fixed conditions; changing parameters is not available yet."
                                color: page.theme.muted
                                font.family: "Segoe UI"
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }
                        }
                        Button {
                            id: runExperimentButton
                            Layout.alignment: Qt.AlignRight
                            text: "Run experiment"
                            enabled: page.viewModel && page.viewModel.hasDigitsDataset
                            onClicked: page.viewModel.runDimensionalityExperiments()
                            contentItem: Text {
                                text: runExperimentButton.text
                                color: "#FFFFFF"
                                font.family: "Bahnschrift"
                                font.pixelSize: 10
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle { radius: 4; color: runExperimentButton.enabled ? page.theme.accent : "#A8B3AC" }
                        }
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 300
                    Layout.fillHeight: true
                    radius: 6
                    color: "#E9EEE8"
                    border.color: "#D8E0D7"
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 12
                        Text {
                            text: "COMPARISON PRINCIPLE"
                            color: page.theme.green
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.weight: Font.Bold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Change one factor at a time"
                            color: page.theme.ink
                            font.family: "Bahnschrift"
                            font.pixelSize: 18
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            text: "Keep the dataset, feature construction, distance definition, and evaluation protocol fixed while varying dimensionality. The run action uses the reproducible defaults shown here."
                            color: page.theme.muted
                            font.family: "Segoe UI"
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                            verticalAlignment: Text.AlignTop
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 260
                radius: 6
                color: page.theme.surface
                border.color: page.theme.line
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 12
                    Text {
                        text: "EXPERIMENT SUMMARY"
                        color: page.theme.green
                        font.family: "Bahnschrift"
                        font.pixelSize: 9
                        font.weight: Font.Bold
                    }
                    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: page.theme.line }
                    TextArea {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        text: page.viewModel ? page.viewModel.dimensionalityExperimentSummary : "No experiment output yet."
                        color: page.theme.ink
                        font.family: "Consolas"
                        font.pixelSize: 10
                        wrapMode: TextEdit.WordWrap
                        readOnly: true
                        background: Rectangle { color: "#F7F9F7"; border.color: page.theme.line; radius: 5 }
                    }
                }
            }
        }
    }
}