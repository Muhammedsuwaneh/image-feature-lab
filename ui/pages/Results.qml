pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: page
    objectName: "resultsPage"
    required property var viewModel
    required property var theme

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
                    text: page.viewModel.experimentsRunning ? "Running experiments and rendering charts..."
                        : page.viewModel.experimentError ? "Experiment failed: " + page.viewModel.experimentError
                        : page.viewModel.dimensionalityCharts.length > 0
                        ? "MNIST results: stratified subset of 5,000 training and 1,000 test images; seed 42."
                        : "Run the experiment suite to generate measured results."
                    color: page.theme.muted
                    font.family: "Segoe UI"
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }
                Button {
                    id: runExperimentButton
                    objectName: "runExperimentsButton"
                    text: page.viewModel.datasetLoading ? "Loading dataset..."
                        : page.viewModel.experimentsRunning ? "Running..."
                        : page.viewModel.hasMNISTDataset ? "Run experiments" : "Load dataset and run"
                    enabled: !page.viewModel.datasetLoading && !page.viewModel.experimentsRunning
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
                            model: ["CONDITION", "FEATURES", "MEAN DIST.", "DIST. STD", "DIST. CV", "MEAN CONTRAST", "ACCURACY"]
                            Text {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredWidth: 0
                                Layout.minimumWidth: 0
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
                                model: [comparisonRow.modelData.label, comparisonRow.modelData.feature_count, Number(comparisonRow.modelData.mean_distance).toFixed(3), Number(comparisonRow.modelData.distance_std).toFixed(3), Number(comparisonRow.modelData.coefficient_of_variation).toFixed(3), Number(comparisonRow.modelData.relative_contrast).toFixed(3), (Number(comparisonRow.modelData.test_accuracy) * 100).toFixed(2) + "%"]
                                Text {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 0
                                    Layout.minimumWidth: 0
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
                                objectName: "resultChartImage"
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
