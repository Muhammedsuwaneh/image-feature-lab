import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: emptyState
    property var theme
    property string marker: "--"
    property string title: ""
    property string detail: ""
    spacing: 9

    Rectangle {
        Layout.preferredWidth: 34
        Layout.preferredHeight: 34
        radius: 6
        color: emptyState.theme.paleGreen

        Text {
            anchors.centerIn: parent
            text: emptyState.marker
            color: emptyState.theme.green
            font.family: "Bahnschrift"
            font.pixelSize: 10
            font.weight: Font.Bold
        }
    }

    Text {
        Layout.fillWidth: true
        text: emptyState.title
        color: emptyState.theme.ink
        font.family: "Bahnschrift"
        font.pixelSize: 16
        font.weight: Font.DemiBold
        wrapMode: Text.WordWrap
    }

    Text {
        Layout.fillWidth: true
        text: emptyState.detail
        color: emptyState.theme.muted
        font.family: "Segoe UI"
        font.pixelSize: 11
        wrapMode: Text.WordWrap
    }
}
