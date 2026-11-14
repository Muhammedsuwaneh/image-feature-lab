pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: page
    objectName: "distanceConcentrationPage"
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
                eyebrow: "ANALYSIS / DISTANCE GEOMETRY"
                title: "Distance concentration"
                description: "Measure the distance distribution from one held-out MNIST sample to the training feature space."
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 142
                spacing: 14

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 6
                    color: page.theme.surface
                    border.color: page.theme.line

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 10
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                Layout.fillWidth: true
                                text: "HELD-OUT QUERY"
                                color: page.theme.ink
                                font.family: "Bahnschrift"
                                font.pixelSize: 10
                                font.weight: Font.Bold
                            }
                            Text {
                                text: page.distanceResult.error ? "ANALYSIS ERROR" : (page.distanceResult.query_index !== undefined ? "MEASURED" : "READY")
                                color: page.distanceResult.error ? page.theme.accent : page.theme.green
                                font.family: "Bahnschrift"
                                font.pixelSize: 8
                                font.weight: Font.Bold
                            }
                        }
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: page.theme.line }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 14
                            Text {
                                Layout.fillWidth: true
                                text: "Test split position"
                                color: page.theme.ink
                                font.family: "Segoe UI"
                                font.pixelSize: 11
                            }
                            SpinBox {
                                id: queryPosition
                                from: 1
                                to: Math.max(1, page.viewModel.datasetTestCount)
                                value: 1
                                stepSize: 1
                                editable: true
                            }
                            Button {
                                id: analyzeButton
                                text: page.viewModel.distanceAnalysisRunning ? "Analyzing..." : "Analyze distances"
                                enabled: page.viewModel.hasMNISTDataset && !page.viewModel.distanceAnalysisRunning
                                onClicked: page.viewModel.analyzeDistanceConcentration(queryPosition.value - 1)
                                contentItem: Text {
                                    text: analyzeButton.text
                                    color: "#FFFFFF"
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 10
                                    font.weight: Font.DemiBold
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle { radius: 4; color: analyzeButton.enabled ? page.theme.accent : "#A8B3AC" }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 275
                    Layout.fillHeight: true
                    radius: 6
                    color: "#E9EEE8"
                    border.color: "#D8E0D7"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 13
                        Text {
                            text: "ANALYSIS BASIS"
                            color: page.theme.green
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.weight: Font.Bold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: page.viewModel.hasMNISTDataset
                                ? page.viewModel.datasetSampleCount + " MNIST samples | " + page.viewModel.datasetFeatureCount + " features"
                                : "MNIST dataset unavailable"
                            color: page.theme.ink
                            font.family: "Segoe UI"
                            font.pixelSize: 11
                        }
                        Text {
                            Layout.fillWidth: true
                            text: page.viewModel.hasMNISTDataset
                                ? page.viewModel.datasetTrainCount + " training references | Euclidean distance | test-only query"
                                : page.viewModel.datasetError
                            color: page.theme.muted
                            font.family: "Segoe UI"
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: width < 720 ? 2 : 4
                columnSpacing: 12
                rowSpacing: 12

                MetricTile {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 118
                    theme: page.theme
                    label: "MEAN DISTANCE"
                    value: page.distanceResult.mean_distance !== undefined ? Number(page.distanceResult.mean_distance).toFixed(3) : "--"
                    detail: page.distanceResult.reference_count !== undefined ? "Across " + page.distanceResult.reference_count + " training samples" : "Run analysis to measure"
                    marker: page.theme.green
                }
                MetricTile {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 118
                    theme: page.theme
                    label: "STANDARD DEVIATION"
                    value: page.distanceResult.standard_deviation !== undefined ? Number(page.distanceResult.standard_deviation).toFixed(3) : "--"
                    detail: page.distanceResult.variance !== undefined ? "Variance " + Number(page.distanceResult.variance).toFixed(3) : "Population statistic"
                    marker: page.theme.accent
                }
                MetricTile {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 118
                    theme: page.theme
                    label: "ORDINARY-DISTANCE CV"
                    value: page.distanceResult.coefficient_of_variation !== undefined ? Number(page.distanceResult.coefficient_of_variation).toFixed(4) : "--"
                    detail: "Standard deviation / mean distance"
                    marker: "#3E7890"
                }
                MetricTile {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 118
                    theme: page.theme
                    label: "RELATIVE DISTANCE CONTRAST"
                    value: page.distanceResult.relative_distance_contrast !== undefined ? Number(page.distanceResult.relative_distance_contrast).toFixed(3) : "--"
                    detail: "(Maximum - minimum) / minimum"
                    marker: "#8B6B42"
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 350
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
                        anchors.margins: 18
                        spacing: 8
                        Text {
                            text: "DISTANCE DISTRIBUTION"
                            color: page.theme.ink
                            font.family: "Bahnschrift"
                            font.pixelSize: 10
                            font.weight: Font.Bold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: page.distanceResult.query_index !== undefined
                                ? "Query sample " + page.distanceResult.query_index + " | class " + page.distanceResult.query_label + " | min " + Number(page.distanceResult.minimum_distance).toFixed(3) + " | max " + Number(page.distanceResult.maximum_distance).toFixed(3)
                                : "Distances from the selected held-out sample to every training sample."
                            color: page.theme.muted
                            font.family: "Segoe UI"
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                        }
                        Image {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            source: page.viewModel.distanceConcentrationChart
                            visible: page.viewModel.distanceConcentrationChart.length > 0
                            cache: false
                            fillMode: Image.PreserveAspectFit
                            asynchronous: true
                        }
                        EmptyState {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            theme: page.theme
                            marker: "D"
                            title: page.distanceResult.error ? "Analysis unavailable" : "No measurements yet"
                            detail: page.distanceResult.error || "Choose a held-out test position and run the distance analysis."
                            visible: page.viewModel.distanceConcentrationChart.length === 0
                        }
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 280
                    Layout.fillHeight: true
                    radius: 6
                    color: page.theme.surface
                    border.color: page.theme.line
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12
                        Text {
                            text: "EXTREME DISTANCES"
                            color: page.theme.ink
                            font.family: "Bahnschrift"
                            font.pixelSize: 10
                            font.weight: Font.Bold
                        }
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: page.theme.line }
                        Text {
                            text: "NEAREST TRAINING SAMPLE"
                            color: page.theme.green
                            font.family: "Bahnschrift"
                            font.pixelSize: 8
                            font.weight: Font.Bold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: page.distanceResult.nearest_sample_index !== undefined
                                ? "Sample " + page.distanceResult.nearest_sample_index + " | class " + page.distanceResult.nearest_sample_label + " | " + Number(page.distanceResult.nearest_distance).toFixed(3)
                                : "--"
                            color: page.theme.ink
                            font.family: "Segoe UI"
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: page.theme.line }
                        Text {
                            text: "FARTHEST TRAINING SAMPLE"
                            color: page.theme.accent
                            font.family: "Bahnschrift"
                            font.pixelSize: 8
                            font.weight: Font.Bold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: page.distanceResult.farthest_sample_index !== undefined
                                ? "Sample " + page.distanceResult.farthest_sample_index + " | class " + page.distanceResult.farthest_sample_label + " | " + Number(page.distanceResult.farthest_distance).toFixed(3)
                                : "--"
                            color: page.theme.ink
                            font.family: "Segoe UI"
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Item { Layout.fillHeight: true }
                        Text {
                            Layout.fillWidth: true
                            text: page.distanceResult.query_index !== undefined
                                ? "Held-out query class " + page.distanceResult.query_label + "; reference set excludes this sample."
                                : "The query is selected from the held-out test split."
                            color: page.theme.muted
                            font.family: "Segoe UI"
                            font.pixelSize: 9
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }
    }

    property var distanceResult: page.viewModel ? page.viewModel.distanceConcentrationResult : ({})
}
