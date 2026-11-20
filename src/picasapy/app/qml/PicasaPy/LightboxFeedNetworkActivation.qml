import QtQuick

Item {
    visible: false
    width: 0
    height: 0
    required property var feed

    Connections {
        target: feed.appWindow
        function onViewerOpenChanged() {
            if (!feed.slowNetworkFolder) {
                viewerFeedActivationTimer.stop()
                viewerFeedCacheRamp.stop()
                feed.feedCacheBuffer = 600
                feed.feedActivationReady = true
            } else if (feed.appWindow.viewerOpen) {
                viewerFeedActivationTimer.stop()
                viewerFeedCacheRamp.stop()
                feed.feedCacheBuffer = 0
                feed.feedActivationReady = false
                return
            } else {
                viewerFeedActivationTimer.restart()
            }
        }
    }

    Connections {
        target: feed
        function onSlowNetworkFolderChanged() {
            if (!feed.slowNetworkFolder) {
                viewerFeedActivationTimer.stop()
                viewerFeedCacheRamp.stop()
                feed.feedCacheBuffer = 600
                feed.feedActivationReady = true
            } else if (feed.appWindow.viewerOpen) {
                viewerFeedActivationTimer.stop()
                viewerFeedCacheRamp.stop()
                feed.feedCacheBuffer = 0
                feed.feedActivationReady = false
            }
        }
    }

    Timer {
        id: viewerFeedActivationTimer
        interval: 100
        repeat: false
        onTriggered: {
            if (!feed.appWindow.viewerOpen) {
                feed.feedCacheBuffer = 0
                feed.feedActivationReady = true
                viewerFeedCacheRamp.start()
            }
        }
    }

    Timer {
        id: viewerFeedCacheRamp
        interval: 16
        repeat: true
        onTriggered: {
            if (feed.appWindow.viewerOpen) {
                stop()
                return
            }
            if (feed.feedCacheBuffer >= 600) {
                stop()
                return
            }
            feed.feedCacheBuffer = Math.min(
                600, feed.feedCacheBuffer + 100)
        }
    }

    Connections {
        target: feed.appWindow
        function onViewerOpenChanged() {
            if (!feed.slowNetworkFolder || feed.appWindow.viewerOpen)
                return
            Qt.callLater(function() {
                if (feed.appWindow.viewerOpen)
                    return
                if (feed.revealAfterViewer) {
                    feed.applyRevealAfterViewer()
                    return
                }
                feed.restoring = true
                feed.restoreAnchor()
                feed.restoring = false
            })
        }
    }
}
