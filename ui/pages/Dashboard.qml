pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: page
    objectName: "dashboardPage"
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
                eyebrow: "PROJECT / OVERVIEW"
                title: "Distance geometry, made visible."
                description: "Investigate how image feature dimensions shape pairwise distances and nearest-neighbor decisions."
            }

            GridLayout {
                Layout.fillWidth: true
                columns: 3
                columnSpacing: 12
                rowSpacing: 12

                MetricTile {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 112
                    theme: page.theme
                    label: "DATASET"
                        value: page.viewModel.datasetLoading ? "Loading..."
                            : page.viewModel.hasDigitsDataset ? "Digits baseline"
                            : page.viewModel.datasetError ? "Load failed" : "Not loaded"
                        detail: page.viewModel.hasDigitsDataset
                            ? page.viewModel.datasetSampleCount + " images / " + page.viewModel.datasetClassCount + " classes"
                            : page.viewModel.datasetError
                    marker: page.theme.accent
                }
                MetricTile {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 112
                    theme: page.theme
                    label: "FEATURE SPACE"
                          value: page.viewModel.hasDigitsDataset
                              ? page.viewModel.datasetFeatureCount + " dimensions"
                              : "Not available"
                          detail: "8 x 8 grayscale pixels / intensities 0-16"
                    marker: page.theme.green
                }
                MetricTile {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 112
                    theme: page.theme
                    label: "CLASSIFICATION"
                    value: page.viewModel.knnEvaluationRunning ? "Evaluating..." : page.viewModel.hasKnnEvaluation
                        ? (page.viewModel.knnTestAccuracy * 100).toFixed(2) + "%"
                        : "Not evaluated"
                    detail: page.viewModel.knnEvaluationError ? page.viewModel.knnEvaluationError : page.viewModel.hasDigitsDataset
                        ? "k = " + page.viewModel.knnK + " / Euclidean distance"
                        : "No nearest-neighbor experiment has run"
                    marker: "#879A8D"
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.minimumHeight: 270
                spacing: 14

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 350
                    radius: 6
                    color: page.theme.surface
                    border.color: page.theme.line

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 22
                        spacing: 12
                        Text {
                            text: "RESEARCH QUESTION"
                            color: page.theme.green
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.weight: Font.Bold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "When do distances stop distinguishing images?"
                            color: page.theme.ink
                            font.family: "Bahnschrift"
                            font.pixelSize: 21
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            text: "The study examines distance concentration in image feature spaces and its relationship to nearest-neighbor classification. Results will be shown here only after they are produced by an experiment."
                            color: page.theme.muted
                            font.family: "Segoe UI"
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                            verticalAlignment: Text.AlignTop
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: page.theme.line
                        }
                        Text {
                            text: "ESTU  /  BIL537 MATHEMATICS FOR ARTIFICIAL INTELLIGENCE"
                            color: page.theme.muted
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.weight: Font.Bold
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 300
                    radius: 6
                    color: "#E9EEE8"
                    border.color: "#D8E0D7"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 22
                        spacing: 13
                        Text {
                            text: "WORKFLOW STATUS"
                            color: page.theme.green
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.weight: Font.Bold
                        }
                        Repeater {
                            model: [
                                { step: "01", name: "Load Digits baseline", state: page.viewModel.datasetLoading ? "LOADING" : page.viewModel.hasDigitsDataset ? "READY" : "NOT LOADED" },
                                { step: "02", name: "Extract feature vectors", state: page.viewModel.hasDigitsDataset ? "READY" : "PENDING" },
                                { step: "03", name: "Compare distances", state: page.viewModel.experimentsRunning ? "RUNNING" : page.viewModel.dimensionalityCharts.length > 0 ? "COMPLETE" : "PENDING" },
                                { step: "04", name: "Evaluate neighbors", state: page.viewModel.knnEvaluationRunning ? "RUNNING" : page.viewModel.hasKnnEvaluation ? "COMPLETE" : "PENDING" }
                            ]
                            delegate: RowLayout {
                                id: workflowStep
                                required property var modelData
                                Layout.fillWidth: true
                                spacing: 10
                                Text {
                                    text: workflowStep.modelData.step
                                    color: page.theme.accent
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 10
                                    font.weight: Font.Bold
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: workflowStep.modelData.name
                                    color: page.theme.ink
                                    font.family: "Segoe UI"
                                    font.pixelSize: 11
                                    elide: Text.ElideRight
                                }
                                Text {
                                    text: workflowStep.modelData.state
                                    color: page.theme.muted
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 8
                                    font.weight: Font.Bold
                                }
                            }
                        }
                        Item { Layout.fillHeight: true }
                        Text {
                            Layout.fillWidth: true
                                text: page.viewModel.hasDigitsDataset
                                    ? page.viewModel.datasetTrainCount + " training / " + page.viewModel.datasetTestCount + " test samples. " + (page.viewModel.experimentsRunning ? "Experiments running." : page.viewModel.dimensionalityCharts.length > 0 ? "Experiment results are ready." : "Ready to run experiments.")
                                    : page.viewModel.datasetError
                            color: page.theme.muted
                            font.family: "Segoe UI"
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }
    }
}
