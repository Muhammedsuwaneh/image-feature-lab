pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: sidebar
    color: theme.rail
    property var viewModel
    property var theme

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 18
        anchors.rightMargin: 18
        anchors.topMargin: 24
        anchors.bottomMargin: 18
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.bottomMargin: 40
            spacing: 11

            Rectangle {
                Layout.preferredWidth: 38
                Layout.preferredHeight: 38
                radius: 7
                color: "#294139"
                border.color: "#496257"

                Column {
                    anchors.centerIn: parent
                    spacing: 3
                    Rectangle { width: 17; height: 2; color: "#E2A08B" }
                    Rectangle { width: 12; height: 2; color: "#C3D3C8" }
                    Rectangle { width: 7; height: 2; color: "#C3D3C8" }
                }
            }

            ColumnLayout {
                spacing: 2
                Text {
                    text: "FEATURELAB"
                    color: "#F2F4F0"
                    font.family: "Bahnschrift"
                    font.pixelSize: 16
                    font.weight: Font.Bold
                }
                Text {
                    text: "IMAGE FEATURE RESEARCH"
                    color: sidebar.theme.railMuted
                    font.family: "Bahnschrift"
                    font.pixelSize: 8
                    font.weight: Font.Bold
                }
            }
        }

        Text {
            Layout.leftMargin: 10
            Layout.bottomMargin: 12
            text: "WORKSPACE"
            color: "#82988D"
            font.family: "Bahnschrift"
            font.pixelSize: 9
            font.weight: Font.Bold
        }

        Repeater {
            model: ListModel {
                ListElement { pageId: "Dashboard"; label: "Dashboard"; indexLabel: "01" }
                ListElement { pageId: "ImageAnalysis"; label: "Image Analysis"; indexLabel: "02" }
                ListElement { pageId: "DistanceConcentration"; label: "Distance Concentration"; indexLabel: "03" }
                ListElement { pageId: "DimensionalityExperiments"; label: "Dimensionality Experiments"; indexLabel: "04" }
                ListElement { pageId: "Results"; label: "Results"; indexLabel: "05" }
            }

            delegate: Button {
                id: navigationButton
                required property string pageId
                required property string label
                required property string indexLabel
                Layout.fillWidth: true
                Layout.preferredHeight: 46
                Layout.bottomMargin: 4
                onClicked: sidebar.viewModel.navigateTo(pageId)

                background: Rectangle {
                    radius: 5
                    color: sidebar.viewModel.currentPage === navigationButton.pageId
                           ? "#2A433A"
                           : navigationButton.hovered ? "#20372F" : "transparent"

                    Rectangle {
                        visible: sidebar.viewModel.currentPage === navigationButton.pageId
                        width: 3
                        radius: 2
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        color: sidebar.theme.accent
                    }
                }

                contentItem: RowLayout {
                    spacing: 11
                    Text {
                        Layout.leftMargin: 10
                        text: navigationButton.indexLabel
                        color: sidebar.viewModel.currentPage === navigationButton.pageId
                               ? "#E5A28D" : "#81958B"
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        font.weight: Font.Bold
                    }
                    Text {
                        Layout.fillWidth: true
                        text: navigationButton.label
                        color: sidebar.viewModel.currentPage === navigationButton.pageId
                               ? "#F2F4F0" : sidebar.theme.railMuted
                        font.family: "Bahnschrift"
                        font.pixelSize: 12
                        font.weight: sidebar.viewModel.currentPage === navigationButton.pageId
                                     ? Font.DemiBold : Font.Normal
                        elide: Text.ElideRight
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: "#344840"
            Layout.bottomMargin: 15
        }

        Text {
            text: "FEATURELAB | 2026"
            color: "#D3DDD6"
            font.family: "Bahnschrift"
            font.pixelSize: 10
            font.weight: Font.Bold
        }
        Text {
            Layout.topMargin: 4
            text: "Distance concentration"
            color: sidebar.theme.railMuted
            font.family: "Segoe UI"
            font.pixelSize: 10
        }
    }
}