pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: page
    objectName: "resultsPage"
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
                eyebrow: "OUTPUT / EXPERIMENT RESULTS"
                title: "Evidence, not estimates."
                description: "Compare measured distance behavior and nearest-neighbor performance after experiments have completed."
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12
                Text {
                    Layout.fillWidth: true
                    text: page.viewModel.dimensionalityCharts.length > 0
                        ? "Results reflect the latest completed experiment run."
                        : "Run the experiment suite to generate measured results."
                    color: page.theme.muted
                    font.family: "Segoe UI"
                    font.pixelSize: 11
                }
                Button {
                    id: runExperimentButton
                    text: "Run experiments"
                    enabled: page.viewModel.hasDigitsDataset
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

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: comparisonColumn.implicitHeight + 36
                radius: 6
                color: page.theme.surface
                border.color: page.theme.line
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 10
                    id: comparisonColumn
                    Text {
                        text: "EXPERIMENT RECORDS"
                        color: page.theme.ink
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        font.weight: Font.Bold
                    }
                    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: page.theme.line }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Repeater {
                            model: ["CONDITION", "FEATURES", "MEAN NN DIST.", "NN CV", "REL. CONTRAST", "ACCURACY"]
                            Text {
                                required property var modelData
                                Layout.fillWidth: true
                                text: modelData
                                color: page.theme.muted
                                font.family: "Bahnschrift"
                                font.pixelSize: 8
                                font.weight: Font.Bold
                            }
                        }
                    }
                    Repeater {
                        model: page.viewModel.dimensionalityComparisonRows
                        RowLayout {
                            id: comparisonRow
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: 10
                            Repeater {
                                model: [comparisonRow.modelData.label, comparisonRow.modelData.feature_count, Number(comparisonRow.modelData.mean_distance).toFixed(3), Number(comparisonRow.modelData.coefficient_of_variation).toFixed(3), Number(comparisonRow.modelData.relative_contrast).toFixed(3), (Number(comparisonRow.modelData.test_accuracy) * 100).toFixed(2) + "%"]
                                Text {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    text: modelData
                                    color: page.theme.ink
                                    font.family: "Segoe UI"
                                    font.pixelSize: 10
                                    elide: Text.ElideRight
                                }
                            }
                        }
                    }
                    EmptyState {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 72
                        theme: page.theme
                        marker: "R"
                        title: "No experiment results"
                        detail: "The table and charts will show measured outputs after an experiment run."
                        visible: page.viewModel.dimensionalityComparisonRows.length === 0
                    }
                }
            }

            GridLayout {
                id: chartGrid
                Layout.fillWidth: true
                columns: width < 760 ? 1 : 2
                columnSpacing: 14
                rowSpacing: 14

                Repeater {
                    model: page.viewModel.dimensionalityCharts
                    Rectangle {
                        id: chartDelegate
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 350
                        Layout.minimumWidth: 320
                        radius: 6
                        color: page.theme.surface
                        border.color: page.theme.line

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 6
                            Text {
                                Layout.fillWidth: true
                                text: chartDelegate.modelData.title
                                color: page.theme.ink
                                font.family: "Bahnschrift"
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                            }
                            Text {
                                Layout.fillWidth: true
                                text: chartDelegate.modelData.caption
                                color: page.theme.muted
                                font.family: "Segoe UI"
                                font.pixelSize: 9
                                wrapMode: Text.WordWrap
                            }
                            Image {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                source: chartDelegate.modelData.source
                                cache: false
                                fillMode: Image.PreserveAspectFit
                                asynchronous: true
                            }
                        }
                    }
                }
            }
        }
    }
}