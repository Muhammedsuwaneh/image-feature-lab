pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: page
    objectName: "distanceConcentrationPage"
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
                eyebrow: "ANALYSIS / DISTANCE GEOMETRY"
                title: "Distance concentration"
                description: "Examine how the spread of pairwise image distances changes in higher-dimensional feature spaces."
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.minimumHeight: 360
                spacing: 14

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 470
                    radius: 6
                    color: page.theme.surface
                    border.color: page.theme.line

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 12
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                Layout.fillWidth: true
                                text: "PAIRWISE DISTANCE DISTRIBUTION"
                                color: page.theme.ink
                                font.family: "Bahnschrift"
                                font.pixelSize: 10
                                font.weight: Font.Bold
                            }
                            Text {
                                text: "NO MEASUREMENTS"
                                color: page.theme.accent
                                font.family: "Bahnschrift"
                                font.pixelSize: 8
                                font.weight: Font.Bold
                            }
                        }
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: page.theme.line }
                        Item {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            EmptyState {
                                anchors.centerIn: parent
                                width: Math.min(parent.width - 32, 350)
                                theme: page.theme
                                marker: "D"
                                title: "No distance distribution available"
                                detail: "Load image data and compute feature vectors before pairwise distances can be measured. No chart is shown until real measurements exist."
                            }
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
                        spacing: 13
                        Text {
                            text: "REQUIRED INPUTS"
                            color: page.theme.green
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.weight: Font.Bold
                        }
                        Repeater {
                            model: ["Image dataset", "Feature representation", "Distance metric"]
                            delegate: RowLayout {
                                id: requiredInput
                                required property string modelData
                                Layout.fillWidth: true
                                spacing: 8
                                Text {
                                    Layout.fillWidth: true
                                    text: requiredInput.modelData
                                    color: page.theme.ink
                                    font.family: "Segoe UI"
                                    font.pixelSize: 11
                                }
                                Text {
                                    text: "PENDING"
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
                            text: "The analysis service will provide the measured distribution and concentration summary."
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