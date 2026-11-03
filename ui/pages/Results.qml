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
                Layout.minimumHeight: 250
                spacing: 14

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 420
                    radius: 6
                    color: page.theme.surface
                    border.color: page.theme.line
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 12
                        Text {
                            text: "METRIC COMPARISON"
                            color: page.theme.ink
                            font.family: "Bahnschrift"
                            font.pixelSize: 10
                            font.weight: Font.Bold
                        }
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: page.theme.line }
                        Item {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            EmptyState {
                                anchors.centerIn: parent
                                width: Math.min(parent.width - 32, 360)
                                theme: page.theme
                                marker: "R"
                                title: "No experiment results"
                                detail: "Charts will be populated from completed runs. The interface will not display example or estimated measurements."
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 290
                    Layout.fillHeight: true
                    radius: 6
                    color: "#E9EEE8"
                    border.color: "#D8E0D7"
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 12
                        Text {
                            text: "RUN SUMMARY"
                            color: page.theme.green
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.weight: Font.Bold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "No run selected"
                            color: page.theme.ink
                            font.family: "Bahnschrift"
                            font.pixelSize: 18
                            font.weight: Font.DemiBold
                        }
                        Text {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            text: "Run metadata and configuration will appear here when the experiment service is available."
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
                Layout.preferredHeight: 190
                radius: 6
                color: page.theme.surface
                border.color: page.theme.line
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 10
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
                        Text { Layout.fillWidth: true; text: "FEATURE DIMENSION"; color: page.theme.muted; font.family: "Bahnschrift"; font.pixelSize: 8; font.weight: Font.Bold }
                        Text { Layout.fillWidth: true; text: "DISTANCE MEASURE"; color: page.theme.muted; font.family: "Bahnschrift"; font.pixelSize: 8; font.weight: Font.Bold }
                        Text { Layout.fillWidth: true; text: "1-NN PERFORMANCE"; color: page.theme.muted; font.family: "Bahnschrift"; font.pixelSize: 8; font.weight: Font.Bold }
                    }
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        EmptyState {
                            anchors.centerIn: parent
                            theme: page.theme
                            marker: "--"
                            title: "No recorded runs"
                            detail: "Completed experiment records will be listed here."
                        }
                    }
                }
            }
        }
    }
}