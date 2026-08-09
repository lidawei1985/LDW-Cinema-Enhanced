# Hardened TVBoxOSC build

This workflow builds commit `e8c12d2bf408feb129857e577803d918e613482f` from the
preserved `no1412/TVBoxOSC` fork of the deleted `CatVodTVOfficial/TVBoxOSC`
repository.

Before building, it removes the bundled Thunder JAR and magnet implementation,
plus phone, location, storage, task-list, and package-install permissions that
are unnecessary for HTTPS TVBox playback.
