import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "../components"

Item {
    id: page
    objectName: "imageAnalysisPage"
    property var viewModel
    property var theme

    FileDialog {
        id: imagePicker
        title: "Select an image"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Image files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)", "All files (*)"]
        onAccepted: page.viewModel.setSelectedImage(selectedFile.toString())
    }

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
                eyebrow: "INPUT / IMAGE INSPECTION"
                title: "Inspect an image before analysis."
                description: "Choose a local image to preview it. Feature extraction and image metadata are not connected yet."
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.minimumHeight: 410
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
                        anchors.margins: 16
                        spacing: 12

                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                Layout.fillWidth: true
                                text: page.viewModel.hasSelectedImage ? page.viewModel.selectedImageName : "IMAGE PREVIEW"
                                color: page.theme.ink
                                font.family: "Bahnschrift"
                                font.pixelSize: 11
                                font.weight: Font.Bold
                                elide: Text.ElideMiddle
                            }
                            Button {
                                id: chooseImageButton
                                text: "Choose image"
                                onClicked: imagePicker.open()
                                contentItem: Text {
                                    text: chooseImageButton.text
                                    color: "#FFFFFF"
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 10
                                    font.weight: Font.DemiBold
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle { radius: 4; color: chooseImageButton.hovered ? "#A94A35" : page.theme.accent }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#F0F3EF"
                            radius: 4
                            clip: true

                            Image {
                                id: imagePreview
                                anchors.fill: parent
                                anchors.margins: 12
                                source: page.viewModel.selectedImageUrl
                                fillMode: Image.PreserveAspectFit
                                asynchronous: true
                                visible: page.viewModel.hasSelectedImage && status === Image.Ready
                            }

                            ColumnLayout {
                                anchors.centerIn: parent
                                width: Math.min(parent.width - 40, 390)
                                spacing: 8
                                visible: !page.viewModel.hasSelectedImage || imagePreview.status === Image.Error

                                Rectangle {
                                    Layout.alignment: Qt.AlignHCenter
                                    Layout.preferredWidth: 46
                                    Layout.preferredHeight: 46
                                    radius: 6
                                    color: page.theme.paleGreen
                                    Text {
                                        anchors.centerIn: parent
                                        text: imagePreview.status === Image.Error ? "!" : "IMG"
                                        color: page.theme.green
                                        font.family: "Bahnschrift"
                                        font.pixelSize: 11
                                        font.weight: Font.Bold
                                    }
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: imagePreview.status === Image.Error ? "This image could not be previewed." : "No image selected"
                                    color: page.theme.ink
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 15
                                    font.weight: Font.DemiBold
                                    horizontalAlignment: Text.AlignHCenter
                                    wrapMode: Text.WordWrap
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: imagePreview.status === Image.Error ? "Choose a supported local image file to try again." : "Select a local image to display it here."
                                    color: page.theme.muted
                                    font.family: "Segoe UI"
                                    font.pixelSize: 11
                                    horizontalAlignment: Text.AlignHCenter
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 290
                    Layout.fillHeight: true
                    radius: 6
                    color: page.theme.surface
                    border.color: page.theme.line

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 14

                        Text {
                            text: "INSPECTION"
                            color: page.theme.green
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.weight: Font.Bold
                        }

                        Text {
                            Layout.fillWidth: true
                            text: page.viewModel.hasSelectedImage ? "Image selected" : "Waiting for input"
                            color: page.theme.ink
                            font.family: "Bahnschrift"
                            font.pixelSize: 18
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }

                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: page.theme.line }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            Text { text: "FILE NAME"; color: page.theme.muted; font.family: "Bahnschrift"; font.pixelSize: 8; font.weight: Font.Bold }
                            Text {
                                Layout.fillWidth: true
                                text: page.viewModel.hasSelectedImage ? page.viewModel.selectedImageName : "Not available"
                                color: page.theme.ink
                                font.family: "Segoe UI"
                                font.pixelSize: 11
                                wrapMode: Text.WrapAnywhere
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            Text { text: "IMAGE DIMENSIONS"; color: page.theme.muted; font.family: "Bahnschrift"; font.pixelSize: 8; font.weight: Font.Bold }
                            Text {
                                text: imagePreview.status === Image.Ready
                                      ? imagePreview.sourceSize.width + " x " + imagePreview.sourceSize.height + " px"
                                      : "Not available"
                                color: page.theme.ink
                                font.family: "Segoe UI"
                                font.pixelSize: 11
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: page.theme.line
                        }

                        EmptyState {
                            Layout.fillWidth: true
                            theme: page.theme
                            marker: "FX"
                            title: "Feature extraction is not connected"
                            detail: "Pixel statistics and feature descriptors will appear after the image-processing backend is implemented."
                        }

                        Item { Layout.fillHeight: true }

                        Button {
                            id: clearImageButton
                            Layout.fillWidth: true
                            visible: page.viewModel.hasSelectedImage
                            text: "Clear image"
                            onClicked: page.viewModel.clearSelectedImage()
                            contentItem: Text {
                                text: clearImageButton.text
                                color: page.theme.ink
                                font.family: "Bahnschrift"
                                font.pixelSize: 10
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle { radius: 4; color: "#F1F3EE"; border.color: page.theme.line }
                        }
                    }
                }
            }
        }
    }
}