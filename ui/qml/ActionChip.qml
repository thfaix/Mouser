import QtQuick
import "Theme.js" as Theme

/*  A single action chip for the action picker.  */

Rectangle {
    id: chip
    readonly property bool darkMode: uiState ? uiState.darkMode : false
    readonly property string fontFamily: uiState ? uiState.fontFamily : ""
    readonly property var theme: Theme.palette(chip.darkMode)

    property string actionId: ""
    property string actionLabel: ""
    property bool isCurrent: false

    signal picked(string aid)

    width: chipText.implicitWidth + 24
    height: 34
    radius: 9
    activeFocusOnTab: true

    Accessible.role: Accessible.Button
    Accessible.name: actionLabel

    color: isCurrent
           ? theme.accent
           : chipMa.containsMouse
             ? theme.bgCardHover
             : theme.bgCard
    border.width: activeFocus ? 2 : 1
    border.color: isCurrent ? theme.accent : activeFocus ? theme.accent : theme.border

    Behavior on color { ColorAnimation { duration: 120 } }

    Keys.onReturnPressed: chip.picked(actionId)
    Keys.onEnterPressed: chip.picked(actionId)
    Keys.onSpacePressed: chip.picked(actionId)

    Text {
        id: chipText
        anchors.centerIn: parent
        text: actionLabel
        font { family: chip.fontFamily; pixelSize: 12 }
        color: isCurrent ? theme.bgSidebar : theme.textPrimary
    }

    MouseArea {
        id: chipMa
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: chip.picked(actionId)
    }
}
