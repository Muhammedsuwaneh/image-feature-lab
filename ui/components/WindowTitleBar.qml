import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: titleBar
    objectName: "customTitleBar"
    required property var applicationWindow
    required property var theme
    implicitHeight: 38
    color: theme.rail

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 10
        spacing: 12

        Text {
            text: "FeatureLab"
            color: "#F1F3EE"
            font.family: "Bahnschrift"
            font.pixelSize: 12
            font.weight: Font.DemiBold
        }

        Item { Layout.fillWidth: true }

        ToolButton {
            id: closeButton
            objectName: "closeWindowButton"
            implicitWidth: 34
            implicitHeight: 34
            Accessible.name: "Close FeatureLab"
            ToolTip.visible: hovered
            ToolTip.text: "Close"
            onClicked: titleBar.applicationWindow.close()

            background: Rectangle {
                color: "transparent"
                radius: 6
                border.width: closeButton.activeFocus ? 1 : 0
                border.color: "#A8B9B0"
            }

            contentItem: Item {
                Rectangle {
                    anchors.centerIn: parent
                    width: 16
                    height: 16
                    radius: 8
                    color: closeButton.down ? "#D9443D" : "#FF5F57"
                    border.color: "#E0443E"
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "\u00d7"
                        color: "#65130F"
                        font.family: "Segoe UI"
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        visible: closeButton.hovered || closeButton.activeFocus
                    }
                }
            }
        }
    }
}
