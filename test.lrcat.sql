BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "Adobe_AdditionalMetadata" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"additionalInfoSet"	INTEGER NOT NULL DEFAULT 0,
	"embeddedXmp"	INTEGER NOT NULL DEFAULT 0,
	"externalXmpIsDirty"	INTEGER NOT NULL DEFAULT 0,
	"image"	INTEGER,
	"incrementalWhiteBalance"	INTEGER NOT NULL DEFAULT 0,
	"internalXmpDigest"	,
	"isRawFile"	INTEGER NOT NULL DEFAULT 0,
	"lastSynchronizedHash"	,
	"lastSynchronizedTimestamp"	 NOT NULL DEFAULT -63113817600,
	"metadataPresetID"	,
	"metadataVersion"	,
	"monochrome"	INTEGER NOT NULL DEFAULT 0,
	"xmp"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_faceProperties" (
	"id_local"	INTEGER,
	"face"	INTEGER,
	"propertiesString"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_imageDevelopBeforeSettings" (
	"id_local"	INTEGER,
	"beforeDigest"	,
	"beforeHasDevelopAdjustments"	,
	"beforePresetID"	,
	"beforeText"	,
	"developSettings"	INTEGER,
	"hasBigData"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_imageDevelopSettings" (
	"id_local"	INTEGER,
	"allowFastRender"	INTEGER,
	"beforeSettingsIDCache"	,
	"croppedHeight"	,
	"croppedWidth"	,
	"digest"	,
	"fileHeight"	,
	"fileWidth"	,
	"filterHeight"	,
	"filterWidth"	,
	"grayscale"	INTEGER,
	"hasAIMasks"	INTEGER NOT NULL DEFAULT 0,
	"hasBigData"	INTEGER NOT NULL DEFAULT 0,
	"hasDevelopAdjustments"	INTEGER,
	"hasDevelopAdjustmentsEx"	,
	"hasLensBlur"	INTEGER NOT NULL DEFAULT 0,
	"hasMasks"	INTEGER NOT NULL DEFAULT 0,
	"hasPointColor"	INTEGER NOT NULL DEFAULT 0,
	"hasRetouch"	,
	"hasSettings1"	,
	"hasSettings2"	,
	"historySettingsID"	,
	"image"	INTEGER,
	"isHdrEditMode"	INTEGER NOT NULL DEFAULT 0,
	"processVersion"	,
	"profileCorrections"	,
	"removeChromaticAberration"	,
	"settingsID"	,
	"snapshotID"	,
	"text"	,
	"validatedForVersion"	,
	"whiteBalance"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_imageProofSettings" (
	"id_local"	INTEGER,
	"colorProfile"	,
	"image"	INTEGER,
	"renderingIntent"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_imageProperties" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"image"	INTEGER,
	"propertiesString"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_images" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"aspectRatioCache"	 NOT NULL DEFAULT -1,
	"bitDepth"	 NOT NULL DEFAULT 0,
	"captureTime"	,
	"colorChannels"	 NOT NULL DEFAULT 0,
	"colorLabels"	 NOT NULL DEFAULT '',
	"colorMode"	 NOT NULL DEFAULT -1,
	"copyCreationTime"	 NOT NULL DEFAULT -63113817600,
	"copyName"	,
	"copyReason"	,
	"developSettingsIDCache"	,
	"editLock"	INTEGER NOT NULL DEFAULT 0,
	"fileFormat"	 NOT NULL DEFAULT 'unset',
	"fileHeight"	,
	"fileWidth"	,
	"hasMissingSidecars"	INTEGER,
	"masterImage"	INTEGER,
	"orientation"	,
	"originalCaptureTime"	,
	"originalRootEntity"	INTEGER,
	"panningDistanceH"	,
	"panningDistanceV"	,
	"pick"	 NOT NULL DEFAULT 0,
	"positionInFolder"	 NOT NULL DEFAULT 'z',
	"propertiesCache"	,
	"pyramidIDCache"	,
	"rating"	,
	"rootFile"	INTEGER NOT NULL DEFAULT 0,
	"sidecarStatus"	,
	"touchCount"	 NOT NULL DEFAULT 0,
	"touchTime"	 NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_libraryImageDevelop3DLUTColorTable" (
	"id_local"	INTEGER,
	"LUTFullString"	,
	"LUTHash"	 UNIQUE,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_libraryImageDevelopHistoryStep" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"dateCreated"	,
	"digest"	,
	"hasBigData"	INTEGER NOT NULL DEFAULT 0,
	"hasDevelopAdjustments"	,
	"image"	INTEGER,
	"name"	,
	"relValueString"	,
	"text"	,
	"valueString"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_libraryImageDevelopSnapshot" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"digest"	,
	"hasBigData"	INTEGER NOT NULL DEFAULT 0,
	"hasDevelopAdjustments"	,
	"image"	INTEGER,
	"locked"	,
	"name"	,
	"snapshotID"	,
	"text"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_libraryImageFaceProcessHistory" (
	"id_local"	INTEGER,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"lastFaceDetector"	,
	"lastFaceRecognizer"	,
	"lastImageIndexer"	,
	"lastImageOrientation"	,
	"lastTryStatus"	,
	"userTouched"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_namedIdentityPlate" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"description"	,
	"identityPlate"	,
	"identityPlateHash"	,
	"moduleFont"	,
	"moduleSelectedTextColor"	,
	"moduleTextColor"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_variables" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"name"	,
	"value"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "Adobe_variablesTable" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"name"	,
	"type"	,
	"value"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgDNGProxyInfo" (
	"id_local"	INTEGER,
	"fileUUID"	 NOT NULL DEFAULT '',
	"status"	 NOT NULL DEFAULT 'U',
	"statusDateTime"	 NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgDNGProxyInfoUpdater" (
	"id_local"	INTEGER,
	"taskID"	 NOT NULL DEFAULT '' UNIQUE,
	"taskStatus"	 NOT NULL DEFAULT 'pending',
	"whenPosted"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgDeletedOzAlbumAssetIds" (
	"id_local"	 NOT NULL DEFAULT 0,
	"ozCatalogId"	 NOT NULL,
	"ozAlbumAssetId"	 NOT NULL,
	"changeCounter"	 DEFAULT 0,
	"lastSyncedChangeCounter"	 DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "AgDeletedOzAlbumIds" (
	"id_local"	 NOT NULL DEFAULT 0,
	"ozCatalogId"	 NOT NULL,
	"ozAlbumId"	 NOT NULL,
	"changeCounter"	 DEFAULT 0,
	"lastSyncedChangeCounter"	 DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "AgDeletedOzAssetIds" (
	"id_local"	 NOT NULL DEFAULT 0,
	"ozCatalogId"	 NOT NULL,
	"ozAssetId"	 NOT NULL,
	"changeCounter"	 DEFAULT 0,
	"lastSyncedChangeCounter"	 DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "AgDeletedOzSpaceIds" (
	"id_local"	 NOT NULL DEFAULT 0,
	"ozCatalogId"	 NOT NULL,
	"ozSpaceId"	 NOT NULL,
	"changeCounter"	 DEFAULT 0,
	"lastSyncedChangeCounter"	 DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "AgDevelopAdditionalMetadata" (
	"id_local"	INTEGER,
	"caiAuthenticationInfo"	,
	"hasCAISign"	INTEGER,
	"hasDepthMap"	INTEGER,
	"hasEnhance"	,
	"image"	INTEGER,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgFolderContent" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"containingFolder"	INTEGER NOT NULL DEFAULT 0,
	"content"	,
	"name"	,
	"owningModule"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgHarvestedDNGMetadata" (
	"id_local"	INTEGER,
	"image"	INTEGER,
	"hasFastLoadData"	INTEGER,
	"hasLossyCompression"	INTEGER,
	"isDNG"	INTEGER,
	"isHDR"	INTEGER,
	"isPano"	INTEGER,
	"isReducedResolution"	INTEGER,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgHarvestedExifMetadata" (
	"id_local"	INTEGER,
	"image"	INTEGER,
	"aperture"	,
	"cameraModelRef"	INTEGER,
	"cameraSNRef"	INTEGER,
	"dateDay"	,
	"dateMonth"	,
	"dateYear"	,
	"flashFired"	INTEGER,
	"focalLength"	,
	"gpsLatitude"	,
	"gpsLongitude"	,
	"gpsSequence"	 NOT NULL DEFAULT 0,
	"hasGPS"	INTEGER,
	"isoSpeedRating"	,
	"lensRef"	INTEGER,
	"shutterSpeed"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgHarvestedIptcMetadata" (
	"id_local"	INTEGER,
	"image"	INTEGER,
	"cityRef"	INTEGER,
	"copyrightState"	INTEGER,
	"countryRef"	INTEGER,
	"creatorRef"	INTEGER,
	"isoCountryCodeRef"	INTEGER,
	"jobIdentifierRef"	INTEGER,
	"locationDataOrigination"	 NOT NULL DEFAULT 'unset',
	"locationGPSSequence"	 NOT NULL DEFAULT -1,
	"locationRef"	INTEGER,
	"stateRef"	INTEGER,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgHarvestedMetadataWorklist" (
	"id_local"	INTEGER,
	"taskID"	 NOT NULL DEFAULT '' UNIQUE,
	"taskStatus"	 NOT NULL DEFAULT 'pending',
	"whenPosted"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgInternedExifCameraModel" (
	"id_local"	INTEGER,
	"searchIndex"	,
	"value"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgInternedExifCameraSN" (
	"id_local"	INTEGER,
	"searchIndex"	,
	"value"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgInternedExifLens" (
	"id_local"	INTEGER,
	"searchIndex"	,
	"value"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgInternedIptcCity" (
	"id_local"	INTEGER,
	"searchIndex"	,
	"value"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgInternedIptcCountry" (
	"id_local"	INTEGER,
	"searchIndex"	,
	"value"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgInternedIptcCreator" (
	"id_local"	INTEGER,
	"searchIndex"	,
	"value"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgInternedIptcIsoCountryCode" (
	"id_local"	INTEGER,
	"searchIndex"	,
	"value"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgInternedIptcJobIdentifier" (
	"id_local"	INTEGER,
	"searchIndex"	,
	"value"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgInternedIptcLocation" (
	"id_local"	INTEGER,
	"searchIndex"	,
	"value"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgInternedIptcState" (
	"id_local"	INTEGER,
	"searchIndex"	,
	"value"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLastCatalogExport" (
	"image"	INTEGER,
	PRIMARY KEY("image")
);
CREATE TABLE IF NOT EXISTS "AgLibraryBackups" (
	"id_local"	INTEGER,
	"backupPath"	 UNIQUE,
	"backupSize"	,
	"backupCreationTime"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollection" (
	"id_local"	INTEGER,
	"creationId"	 NOT NULL DEFAULT '',
	"genealogy"	 NOT NULL DEFAULT '',
	"imageCount"	,
	"name"	 NOT NULL DEFAULT '',
	"parent"	INTEGER,
	"systemOnly"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionChangeCounter" (
	"collection"	,
	"changeCounter"	 DEFAULT 0,
	"lastSyncedChangeCounter"	 DEFAULT 0,
	PRIMARY KEY("collection")
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionContent" (
	"id_local"	INTEGER,
	"collection"	INTEGER NOT NULL DEFAULT 0,
	"content"	,
	"owningModule"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionCoverImage" (
	"id_local"	 NOT NULL DEFAULT 0,
	"collection"	,
	"collectionImage"	 NOT NULL,
	PRIMARY KEY("collection")
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionImage" (
	"id_local"	INTEGER,
	"collection"	INTEGER NOT NULL DEFAULT 0,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"pick"	 NOT NULL DEFAULT 0,
	"positionInCollection"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionImageChangeCounter" (
	"collectionImage"	,
	"collection"	 NOT NULL,
	"image"	 NOT NULL,
	"changeCounter"	 DEFAULT 0,
	"lastSyncedChangeCounter"	 DEFAULT 0,
	PRIMARY KEY("collectionImage")
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionImageOzAlbumAssetIds" (
	"id_local"	 NOT NULL DEFAULT 0,
	"collectionImage"	 NOT NULL,
	"collection"	 NOT NULL,
	"image"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"ozAlbumAssetId"	 DEFAULT pending
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionImageOzSortOrder" (
	"collectionImage"	,
	"collection"	 NOT NULL,
	"positionInCollection"	 NOT NULL,
	"ozSortOrder"	 NOT NULL,
	PRIMARY KEY("collectionImage")
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionLabel" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"collection"	INTEGER NOT NULL DEFAULT 0,
	"label"	,
	"labelData"	,
	"labelGenerics"	,
	"labelType"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionOzAlbumIds" (
	"id_local"	 NOT NULL DEFAULT 0,
	"collection"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"ozAlbumId"	 DEFAULT pending
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionStack" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"collapsed"	INTEGER NOT NULL DEFAULT 0,
	"collection"	INTEGER NOT NULL DEFAULT 0,
	"text"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionStackData" (
	"stack"	INTEGER,
	"collection"	INTEGER NOT NULL DEFAULT 0,
	"stackCount"	INTEGER NOT NULL DEFAULT 0,
	"stackParent"	INTEGER
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionStackImage" (
	"id_local"	INTEGER,
	"collapsed"	INTEGER NOT NULL DEFAULT 0,
	"collection"	INTEGER NOT NULL DEFAULT 0,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"position"	 NOT NULL DEFAULT '',
	"stack"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionSyncedAlbumData" (
	"collection"	 NOT NULL,
	"payloadKey"	 NOT NULL,
	"payloadData"	 NOT NULL
);
CREATE TABLE IF NOT EXISTS "AgLibraryCollectionTrackedAssets" (
	"collection"	 NOT NULL,
	"ozCatalogId"	 DEFAULT current
);
CREATE TABLE IF NOT EXISTS "AgLibraryFace" (
	"id_local"	INTEGER,
	"bl_x"	,
	"bl_y"	,
	"br_x"	,
	"br_y"	,
	"cluster"	INTEGER,
	"compatibleVersion"	,
	"ignored"	INTEGER,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"imageOrientation"	 NOT NULL DEFAULT '',
	"orientation"	,
	"origination"	 NOT NULL DEFAULT 0,
	"propertiesCache"	,
	"regionType"	 NOT NULL DEFAULT 0,
	"skipSuggestion"	INTEGER,
	"tl_x"	 NOT NULL DEFAULT '',
	"tl_y"	 NOT NULL DEFAULT '',
	"touchCount"	 NOT NULL DEFAULT 0,
	"touchTime"	 NOT NULL DEFAULT -63113817600,
	"tr_x"	,
	"tr_y"	,
	"version"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryFaceCluster" (
	"id_local"	INTEGER,
	"keyFace"	INTEGER,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryFaceData" (
	"id_local"	INTEGER,
	"data"	,
	"face"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryFile" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"baseName"	 NOT NULL DEFAULT '',
	"errorMessage"	,
	"errorTime"	,
	"extension"	 NOT NULL DEFAULT '',
	"externalModTime"	,
	"folder"	INTEGER NOT NULL DEFAULT 0,
	"idx_filename"	 NOT NULL DEFAULT '',
	"importHash"	,
	"lc_idx_filename"	 NOT NULL DEFAULT '',
	"lc_idx_filenameExtension"	 NOT NULL DEFAULT '',
	"md5"	,
	"modTime"	,
	"originalFilename"	 NOT NULL DEFAULT '',
	"sidecarExtensions"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryFileAssetMetadata" (
	"fileId"	,
	"sha256"	 NOT NULL,
	"fileSize"	 DEFAULT 0,
	PRIMARY KEY("fileId")
);
CREATE TABLE IF NOT EXISTS "AgLibraryFolder" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"parentId"	INTEGER,
	"pathFromRoot"	 NOT NULL DEFAULT '',
	"rootFolder"	INTEGER NOT NULL DEFAULT 0,
	"visibility"	INTEGER,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryFolderFavorite" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"favorite"	,
	"folder"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryFolderLabel" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"folder"	INTEGER NOT NULL DEFAULT 0,
	"label"	,
	"labelData"	,
	"labelGenerics"	,
	"labelType"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryFolderStack" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"collapsed"	INTEGER NOT NULL DEFAULT 0,
	"text"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryFolderStackData" (
	"stack"	INTEGER,
	"stackCount"	INTEGER NOT NULL DEFAULT 0,
	"stackParent"	INTEGER
);
CREATE TABLE IF NOT EXISTS "AgLibraryFolderStackImage" (
	"id_local"	INTEGER,
	"collapsed"	INTEGER NOT NULL DEFAULT 0,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"position"	 NOT NULL DEFAULT '',
	"stack"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryIPTC" (
	"id_local"	INTEGER,
	"altTextAccessibility"	,
	"caption"	,
	"copyright"	,
	"extDescrAccessibility"	,
	"image"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryImageAttributes" (
	"id_local"	INTEGER,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"lastExportTimestamp"	 DEFAULT 0,
	"lastPublishTimestamp"	 DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryImageChangeCounter" (
	"image"	,
	"changeCounter"	 DEFAULT 0,
	"lastSyncedChangeCounter"	 DEFAULT 0,
	"changedAtTime"	 DEFAULT '',
	"localTimeOffsetSecs"	 DEFAULT 0,
	PRIMARY KEY("image")
);
CREATE TABLE IF NOT EXISTS "AgLibraryImageOzAssetIds" (
	"id_local"	 NOT NULL DEFAULT 0,
	"image"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"ozAssetId"	 DEFAULT pending,
	"ownedByCatalog"	 DEFAULT 'Y'
);
CREATE TABLE IF NOT EXISTS "AgLibraryImageSaveXMP" (
	"id_local"	INTEGER,
	"taskID"	 NOT NULL DEFAULT '' UNIQUE,
	"taskStatus"	 NOT NULL DEFAULT 'pending',
	"whenPosted"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryImageSearchData" (
	"id_local"	INTEGER,
	"featInfo"	,
	"height"	,
	"idDesc"	,
	"idDescCh"	,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"width"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryImageSyncedAssetData" (
	"image"	 NOT NULL,
	"payloadKey"	 NOT NULL,
	"payloadData"	 NOT NULL
);
CREATE TABLE IF NOT EXISTS "AgLibraryImageXMPUpdater" (
	"id_local"	INTEGER,
	"taskID"	 NOT NULL DEFAULT '' UNIQUE,
	"taskStatus"	 NOT NULL DEFAULT 'pending',
	"whenPosted"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryImport" (
	"id_local"	INTEGER,
	"imageCount"	,
	"importDate"	 NOT NULL DEFAULT '',
	"name"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryImportImage" (
	"id_local"	INTEGER,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"import"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryKeyword" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"dateCreated"	 NOT NULL DEFAULT '',
	"genealogy"	 NOT NULL DEFAULT '',
	"imageCountCache"	 DEFAULT -1,
	"includeOnExport"	INTEGER NOT NULL DEFAULT 1,
	"includeParents"	INTEGER NOT NULL DEFAULT 1,
	"includeSynonyms"	INTEGER NOT NULL DEFAULT 1,
	"keywordType"	,
	"lastApplied"	,
	"lc_name"	,
	"name"	,
	"parent"	INTEGER,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryKeywordCooccurrence" (
	"id_local"	INTEGER,
	"tag1"	 NOT NULL DEFAULT '',
	"tag2"	 NOT NULL DEFAULT '',
	"value"	 NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryKeywordFace" (
	"id_local"	INTEGER,
	"face"	INTEGER NOT NULL DEFAULT 0,
	"keyFace"	INTEGER,
	"rankOrder"	,
	"tag"	INTEGER NOT NULL DEFAULT 0,
	"userPick"	INTEGER,
	"userReject"	INTEGER,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryKeywordImage" (
	"id_local"	INTEGER,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"tag"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryKeywordPopularity" (
	"id_local"	INTEGER,
	"occurrences"	 NOT NULL DEFAULT 0,
	"popularity"	 NOT NULL DEFAULT 0,
	"tag"	 NOT NULL DEFAULT '' UNIQUE,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryKeywordSynonym" (
	"id_local"	INTEGER,
	"keyword"	INTEGER NOT NULL DEFAULT 0,
	"lc_name"	,
	"name"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryOzCommentIds" (
	"ozCatalogId"	 NOT NULL,
	"ozSpaceId"	 NOT NULL,
	"ozAssetId"	 NOT NULL,
	"ozCommentId"	 NOT NULL,
	"timestamp"	 NOT NULL
);
CREATE TABLE IF NOT EXISTS "AgLibraryOzFavoriteIds" (
	"ozCatalogId"	 NOT NULL,
	"ozSpaceId"	 NOT NULL,
	"ozAssetId"	 NOT NULL,
	"ozFavoriteId"	 NOT NULL,
	"timestamp"	 NOT NULL
);
CREATE TABLE IF NOT EXISTS "AgLibraryOzFeedbackInfo" (
	"id_local"	INTEGER,
	"image"	 NOT NULL DEFAULT '',
	"lastFeedbackTime"	,
	"lastReadTime"	,
	"newCommentCount"	 NOT NULL DEFAULT 0,
	"newFavoriteCount"	 NOT NULL DEFAULT 0,
	"ozAssetId"	 NOT NULL DEFAULT '',
	"ozCatalogId"	 NOT NULL DEFAULT '',
	"ozSpaceId"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryPublishedCollection" (
	"id_local"	INTEGER,
	"creationId"	 NOT NULL DEFAULT '',
	"genealogy"	 NOT NULL DEFAULT '',
	"imageCount"	,
	"isDefaultCollection"	,
	"name"	 NOT NULL DEFAULT '',
	"parent"	INTEGER,
	"publishedUrl"	,
	"remoteCollectionId"	,
	"systemOnly"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryPublishedCollectionContent" (
	"id_local"	INTEGER,
	"collection"	INTEGER NOT NULL DEFAULT 0,
	"content"	,
	"owningModule"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryPublishedCollectionImage" (
	"id_local"	INTEGER,
	"collection"	INTEGER NOT NULL DEFAULT 0,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"pick"	 NOT NULL DEFAULT 0,
	"positionInCollection"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryPublishedCollectionLabel" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"collection"	INTEGER NOT NULL DEFAULT 0,
	"label"	,
	"labelData"	,
	"labelGenerics"	,
	"labelType"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryRootFolder" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"absolutePath"	 NOT NULL DEFAULT '' UNIQUE,
	"name"	 NOT NULL DEFAULT '',
	"relativePathFromCatalog"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgLibraryUpdatedImages" (
	"image"	INTEGER,
	PRIMARY KEY("image")
);
CREATE TABLE IF NOT EXISTS "AgMRULists" (
	"id_local"	INTEGER,
	"listID"	 NOT NULL DEFAULT '',
	"timestamp"	 NOT NULL DEFAULT 0,
	"value"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgMetadataSearchIndex" (
	"id_local"	INTEGER,
	"exifSearchIndex"	 NOT NULL DEFAULT '',
	"image"	INTEGER,
	"iptcSearchIndex"	 NOT NULL DEFAULT '',
	"otherSearchIndex"	 NOT NULL DEFAULT '',
	"searchIndex"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgOutputImageAsset" (
	"id_local"	INTEGER,
	"assetId"	 NOT NULL DEFAULT '',
	"collection"	INTEGER NOT NULL DEFAULT 0,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"moduleId"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgOzAssetSettings" (
	"id_local"	INTEGER NOT NULL,
	"image"	,
	"ozCatalogId"	 NOT NULL,
	"sha256"	 NOT NULL,
	"updatedTime"	 NOT NULL,
	PRIMARY KEY("image")
);
CREATE TABLE IF NOT EXISTS "AgOzAuxBinaryMetadata" (
	"auxId"	 NOT NULL,
	"ozAssetId"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"digest"	 NOT NULL,
	"sha256"	 NOT NULL,
	"fileSize"	 DEFAULT 0,
	"type"	 NOT NULL
);
CREATE TABLE IF NOT EXISTS "AgOzCorruptedAuxIds" (
	"auxId"	 NOT NULL,
	"ozAssetId"	 NOT NULL,
	"ozCatalogId"	 NOT NULL
);
CREATE TABLE IF NOT EXISTS "AgOzDocRevIds" (
	"localId"	 NOT NULL,
	"currRevId"	 NOT NULL,
	"docType"	 NOT NULL,
	PRIMARY KEY("localId","docType")
);
CREATE TABLE IF NOT EXISTS "AgOzSpaceAlbumIds" (
	"id_local"	 NOT NULL DEFAULT 0,
	"ozCatalogId"	 NOT NULL,
	"ozAlbumId"	 NOT NULL,
	"ozSpaceId"	 NOT NULL,
	"ozSpaceAlbumId"	 NOT NULL
);
CREATE TABLE IF NOT EXISTS "AgOzSpaceIds" (
	"ozCatalogId"	 NOT NULL,
	"ozSpaceId"	 NOT NULL
);
CREATE TABLE IF NOT EXISTS "AgPendingOzAlbumAssetIds" (
	"ozCatalogId"	 NOT NULL,
	"ozAlbumAssetId"	 NOT NULL,
	"ozAssetId"	 NOT NULL,
	"ozAlbumId"	 NOT NULL,
	"ozSortOrder"	 DEFAULT ,
	"ozIsCover"	 DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "AgPendingOzAssetBinaryDownloads" (
	"ozAssetId"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"whenQueued"	 NOT NULL,
	"path"	 NOT NULL,
	"state"	 DEFAULT master
);
CREATE TABLE IF NOT EXISTS "AgPendingOzAssetDevelopSettings" (
	"ozAssetId"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"payloadHash"	 NOT NULL,
	"developUserUpdated"	
);
CREATE TABLE IF NOT EXISTS "AgPendingOzAssets" (
	"ozAssetId"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"state"	 DEFAULT needs_binary,
	"path"	 NOT NULL,
	"payload"	 NOT NULL
);
CREATE TABLE IF NOT EXISTS "AgPendingOzAuxBinaryDownloads" (
	"auxId"	 NOT NULL,
	"ozAssetId"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"payloadHash"	 NOT NULL,
	"whenQueued"	 NOT NULL,
	"state"	 NOT NULL
);
CREATE TABLE IF NOT EXISTS "AgPendingOzDocs" (
	"id_local"	INTEGER NOT NULL,
	"ozDocId"	,
	"ozCatalogId"	 NOT NULL,
	"state"	 DEFAULT needs_binary,
	"fileName"	 NOT NULL,
	"path"	 NOT NULL,
	"binaryType"	 DEFAULT original,
	"needAux"	 DEFAULT 0,
	"needDevelopXmp"	 DEFAULT 0,
	"needSidecar"	 DEFAULT 0,
	"payload"	 NOT NULL,
	"revId"	 DEFAULT 0,
	"isLibImage"	 DEFAULT 0,
	"isPathChanged"	 DEFAULT 0,
	"errorDescription"	 DEFAULT '',
	PRIMARY KEY("ozDocId")
);
CREATE TABLE IF NOT EXISTS "AgPendingOzUploads" (
	"id_local"	INTEGER NOT NULL,
	"localId"	,
	"ozDocId"	,
	"operation"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"changeCounter"	 DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "AgPhotoComment" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"comment"	,
	"commentRealname"	,
	"commentUsername"	,
	"dateCreated"	,
	"photo"	INTEGER NOT NULL DEFAULT 0,
	"remoteId"	 NOT NULL DEFAULT '',
	"remotePhoto"	INTEGER,
	"url"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgPhotoProperty" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"dataType"	,
	"internalValue"	,
	"photo"	INTEGER NOT NULL DEFAULT 0,
	"propertySpec"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgPhotoPropertyArrayElement" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"arrayIndex"	 NOT NULL DEFAULT '',
	"dataType"	,
	"internalValue"	,
	"photo"	INTEGER NOT NULL DEFAULT 0,
	"propertySpec"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgPhotoPropertySpec" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"flattenedAttributes"	,
	"key"	 NOT NULL DEFAULT '',
	"pluginVersion"	 NOT NULL DEFAULT '',
	"sourcePlugin"	 NOT NULL DEFAULT '',
	"userVisibleName"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgPublishListenerWorklist" (
	"id_local"	INTEGER,
	"taskID"	 NOT NULL DEFAULT '' UNIQUE,
	"taskStatus"	 NOT NULL DEFAULT 'pending',
	"whenPosted"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgRemotePhoto" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"collection"	INTEGER NOT NULL DEFAULT 0,
	"commentCount"	,
	"developSettingsDigest"	,
	"fileContentsHash"	,
	"fileModTimestamp"	,
	"metadataDigest"	,
	"mostRecentCommentTime"	,
	"orientation"	,
	"photo"	INTEGER NOT NULL DEFAULT 0,
	"photoNeedsUpdating"	 DEFAULT 2,
	"publishCount"	,
	"remoteId"	,
	"serviceAggregateRating"	,
	"url"	,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgSearchablePhotoProperty" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"dataType"	,
	"internalValue"	,
	"lc_idx_internalValue"	,
	"photo"	INTEGER NOT NULL DEFAULT 0,
	"propertySpec"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgSearchablePhotoPropertyArrayElement" (
	"id_local"	INTEGER,
	"id_global"	 NOT NULL UNIQUE,
	"arrayIndex"	 NOT NULL DEFAULT '',
	"dataType"	,
	"internalValue"	,
	"lc_idx_internalValue"	,
	"photo"	INTEGER NOT NULL DEFAULT 0,
	"propertySpec"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgSourceColorProfileConstants" (
	"id_local"	INTEGER,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"profileName"	 NOT NULL DEFAULT 'Untagged',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgSpecialSourceContent" (
	"id_local"	INTEGER,
	"content"	,
	"owningModule"	,
	"source"	 NOT NULL DEFAULT '',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgTempImages" (
	"image"	INTEGER,
	PRIMARY KEY("image")
);
CREATE TABLE IF NOT EXISTS "AgUnsupportedOzAssets" (
	"id_local"	INTEGER,
	"ozAssetId"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"path"	 NOT NULL,
	"type"	 NOT NULL,
	"payload"	 NOT NULL,
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "AgVideoInfo" (
	"id_local"	INTEGER,
	"duration"	,
	"frame_rate"	,
	"has_audio"	INTEGER NOT NULL DEFAULT 1,
	"has_video"	INTEGER NOT NULL DEFAULT 1,
	"image"	INTEGER NOT NULL DEFAULT 0,
	"poster_frame"	 NOT NULL DEFAULT '0000000000000000/0000000000000001',
	"poster_frame_set_by_user"	INTEGER NOT NULL DEFAULT 0,
	"trim_end"	 NOT NULL DEFAULT '0000000000000000/0000000000000001',
	"trim_start"	 NOT NULL DEFAULT '0000000000000000/0000000000000001',
	PRIMARY KEY("id_local")
);
CREATE TABLE IF NOT EXISTS "LrMobileSyncChangeCounter" (
	"id"	,
	"changeCounter"	 NOT NULL,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "MigratedCollectionImages" (
	"ozAlbumId"	 NOT NULL,
	"ozAlbumAssetId"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"localCollectionId"	INTEGER NOT NULL,
	"localCollectionImageId"	INTEGER NOT NULL,
	UNIQUE("localCollectionImageId","ozCatalogId")
);
CREATE TABLE IF NOT EXISTS "MigratedCollections" (
	"ozAlbumId"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"ozName"	 NOT NULL,
	"localId"	INTEGER NOT NULL,
	UNIQUE("localId","ozCatalogId")
);
CREATE TABLE IF NOT EXISTS "MigratedImages" (
	"ozAssetId"	 NOT NULL,
	"ozCatalogId"	 NOT NULL,
	"localId"	INTEGER NOT NULL,
	UNIQUE("localId","ozCatalogId")
);
CREATE TABLE IF NOT EXISTS "MigratedInfo" (
	"ozCatalogId"	TEXT,
	"migrationStatus"	 NOT NULL,
	"timestamp"	 NOT NULL,
	PRIMARY KEY("ozCatalogId")
);
CREATE TABLE IF NOT EXISTS "MigrationSchemaVersion" (
	"version"	TEXT,
	PRIMARY KEY("version")
);
CREATE TABLE IF NOT EXISTS "sqlite_stat4" (
	"tbl"	,
	"idx"	,
	"neq"	,
	"nlt"	,
	"ndlt"	,
	"sample"	
);
CREATE INDEX IF NOT EXISTS "index_Adobe_AdditionalMetadata_imageAndStatus" ON "Adobe_AdditionalMetadata" (
	"image",
	"externalXmpIsDirty"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_faceProperties_face" ON "Adobe_faceProperties" (
	"face"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_imageDevelopBeforeSettings_developSettings" ON "Adobe_imageDevelopBeforeSettings" (
	"developSettings"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_imageDevelopSettings_digest" ON "Adobe_imageDevelopSettings" (
	"digest"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_imageDevelopSettings_image" ON "Adobe_imageDevelopSettings" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_imageProofSettings_image" ON "Adobe_imageProofSettings" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_imageProperties_image" ON "Adobe_imageProperties" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_images_captureTime" ON "Adobe_images" (
	"captureTime"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_images_masterImage" ON "Adobe_images" (
	"masterImage"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_images_originalRootEntity" ON "Adobe_images" (
	"originalRootEntity"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_images_ratingAndCaptureTime" ON "Adobe_images" (
	"rating",
	"captureTime"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_images_rootFile" ON "Adobe_images" (
	"rootFile"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_libraryImageDevelopHistoryStep_imageDateCreated" ON "Adobe_libraryImageDevelopHistoryStep" (
	"image",
	"dateCreated"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_libraryImageDevelopSnapshot_image" ON "Adobe_libraryImageDevelopSnapshot" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_libraryImageFaceProcessHistory_image" ON "Adobe_libraryImageFaceProcessHistory" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_namedIdentityPlate_description" ON "Adobe_namedIdentityPlate" (
	"description"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_namedIdentityPlate_identityPlateHash" ON "Adobe_namedIdentityPlate" (
	"identityPlateHash"
);
CREATE INDEX IF NOT EXISTS "index_Adobe_variables_name" ON "Adobe_variables" (
	"name"
);
CREATE INDEX IF NOT EXISTS "index_AgDNGProxyInfoUpdater_statusCluster" ON "AgDNGProxyInfoUpdater" (
	"taskStatus",
	"whenPosted",
	"taskID"
);
CREATE INDEX IF NOT EXISTS "index_AgDNGProxyInfoUpdater_taskIDCluster" ON "AgDNGProxyInfoUpdater" (
	"taskID",
	"whenPosted",
	"taskStatus"
);
CREATE INDEX IF NOT EXISTS "index_AgDNGProxyInfo_statusDateTimeForUUID" ON "AgDNGProxyInfo" (
	"status",
	"statusDateTime",
	"fileUUID"
);
CREATE INDEX IF NOT EXISTS "index_AgDNGProxyInfo_uuidStatusDateTime" ON "AgDNGProxyInfo" (
	"fileUUID",
	"status",
	"statusDateTime"
);
CREATE INDEX IF NOT EXISTS "index_AgDeletedOzAlbumAssetIds_changeCounter" ON "AgDeletedOzAlbumAssetIds" (
	"changeCounter",
	"ozCatalogId",
	"ozAlbumAssetId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgDeletedOzAlbumAssetIds_primaryKey" ON "AgDeletedOzAlbumAssetIds" (
	"ozCatalogId",
	"ozAlbumAssetId"
);
CREATE INDEX IF NOT EXISTS "index_AgDeletedOzAlbumIds_changeCounter" ON "AgDeletedOzAlbumIds" (
	"changeCounter",
	"ozCatalogId",
	"ozAlbumId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgDeletedOzAlbumIds_primaryKey" ON "AgDeletedOzAlbumIds" (
	"ozCatalogId",
	"ozAlbumId"
);
CREATE INDEX IF NOT EXISTS "index_AgDeletedOzAssetIds_changeCounter" ON "AgDeletedOzAssetIds" (
	"changeCounter",
	"ozCatalogId",
	"ozAssetId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgDeletedOzAssetIds_primaryKey" ON "AgDeletedOzAssetIds" (
	"ozCatalogId",
	"ozAssetId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgDeletedOzSpaceIds_primaryKey" ON "AgDeletedOzSpaceIds" (
	"ozCatalogId",
	"ozSpaceId"
);
CREATE INDEX IF NOT EXISTS "index_AgDevelopAdditionalMetadata_image" ON "AgDevelopAdditionalMetadata" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgFolderContent_containingFolder" ON "AgFolderContent" (
	"containingFolder"
);
CREATE INDEX IF NOT EXISTS "index_AgFolderContent_owningModule" ON "AgFolderContent" (
	"owningModule"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedDNGMetadata_byHasFastLoadData" ON "AgHarvestedDNGMetadata" (
	"hasFastLoadData",
	"image",
	"isDNG",
	"hasLossyCompression",
	"isReducedResolution",
	"isPano",
	"isHDR"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedDNGMetadata_byHasLossyCompression" ON "AgHarvestedDNGMetadata" (
	"hasLossyCompression",
	"image",
	"isDNG",
	"hasFastLoadData",
	"isReducedResolution",
	"isPano",
	"isHDR"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedDNGMetadata_byImage" ON "AgHarvestedDNGMetadata" (
	"image",
	"isDNG",
	"hasFastLoadData",
	"hasLossyCompression",
	"isReducedResolution",
	"isPano",
	"isHDR"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedDNGMetadata_byIsDNG" ON "AgHarvestedDNGMetadata" (
	"isDNG",
	"image",
	"hasFastLoadData",
	"hasLossyCompression",
	"isReducedResolution",
	"isPano",
	"isHDR"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedDNGMetadata_byIsHDR" ON "AgHarvestedDNGMetadata" (
	"isHDR",
	"image",
	"isDNG",
	"hasFastLoadData",
	"hasLossyCompression",
	"isReducedResolution",
	"isPano"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedDNGMetadata_byIsPano" ON "AgHarvestedDNGMetadata" (
	"isPano",
	"image",
	"isDNG",
	"hasFastLoadData",
	"hasLossyCompression",
	"isReducedResolution",
	"isHDR"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedDNGMetadata_byIsReducedResolution" ON "AgHarvestedDNGMetadata" (
	"isReducedResolution",
	"image",
	"isDNG",
	"hasFastLoadData",
	"hasLossyCompression",
	"isPano",
	"isHDR"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedExifMetadata_aperture" ON "AgHarvestedExifMetadata" (
	"aperture"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedExifMetadata_cameraModelRef" ON "AgHarvestedExifMetadata" (
	"cameraModelRef"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedExifMetadata_cameraSNRef" ON "AgHarvestedExifMetadata" (
	"cameraSNRef"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedExifMetadata_date" ON "AgHarvestedExifMetadata" (
	"dateYear",
	"dateMonth",
	"dateDay",
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedExifMetadata_flashFired" ON "AgHarvestedExifMetadata" (
	"flashFired"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedExifMetadata_focalLength" ON "AgHarvestedExifMetadata" (
	"focalLength"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedExifMetadata_gpsCluster" ON "AgHarvestedExifMetadata" (
	"hasGPS",
	"gpsLatitude",
	"gpsLongitude",
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedExifMetadata_image" ON "AgHarvestedExifMetadata" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedExifMetadata_isoSpeedRating" ON "AgHarvestedExifMetadata" (
	"isoSpeedRating"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedExifMetadata_lensRef" ON "AgHarvestedExifMetadata" (
	"lensRef"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedExifMetadata_shutterSpeed" ON "AgHarvestedExifMetadata" (
	"shutterSpeed"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedIptcMetadata_cityRef" ON "AgHarvestedIptcMetadata" (
	"cityRef"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedIptcMetadata_copyrightState" ON "AgHarvestedIptcMetadata" (
	"copyrightState"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedIptcMetadata_countryRef" ON "AgHarvestedIptcMetadata" (
	"countryRef"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedIptcMetadata_creatorRef" ON "AgHarvestedIptcMetadata" (
	"creatorRef"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedIptcMetadata_image" ON "AgHarvestedIptcMetadata" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedIptcMetadata_isoCountryCodeRef" ON "AgHarvestedIptcMetadata" (
	"isoCountryCodeRef"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedIptcMetadata_jobIdentifierRef" ON "AgHarvestedIptcMetadata" (
	"jobIdentifierRef"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedIptcMetadata_locationDataOrigination" ON "AgHarvestedIptcMetadata" (
	"locationDataOrigination"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedIptcMetadata_locationRef" ON "AgHarvestedIptcMetadata" (
	"locationRef"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedIptcMetadata_stateRef" ON "AgHarvestedIptcMetadata" (
	"stateRef"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedMetadataWorklist_statusCluster" ON "AgHarvestedMetadataWorklist" (
	"taskStatus",
	"whenPosted",
	"taskID"
);
CREATE INDEX IF NOT EXISTS "index_AgHarvestedMetadataWorklist_taskIDCluster" ON "AgHarvestedMetadataWorklist" (
	"taskID",
	"whenPosted",
	"taskStatus"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedExifCameraModel_searchIndex" ON "AgInternedExifCameraModel" (
	"searchIndex"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedExifCameraModel_value" ON "AgInternedExifCameraModel" (
	"value"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedExifCameraSN_searchIndex" ON "AgInternedExifCameraSN" (
	"searchIndex"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedExifCameraSN_value" ON "AgInternedExifCameraSN" (
	"value"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedExifLens_searchIndex" ON "AgInternedExifLens" (
	"searchIndex"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedExifLens_value" ON "AgInternedExifLens" (
	"value"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcCity_searchIndex" ON "AgInternedIptcCity" (
	"searchIndex"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcCity_value" ON "AgInternedIptcCity" (
	"value"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcCountry_searchIndex" ON "AgInternedIptcCountry" (
	"searchIndex"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcCountry_value" ON "AgInternedIptcCountry" (
	"value"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcCreator_searchIndex" ON "AgInternedIptcCreator" (
	"searchIndex"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcCreator_value" ON "AgInternedIptcCreator" (
	"value"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcIsoCountryCode_searchIndex" ON "AgInternedIptcIsoCountryCode" (
	"searchIndex"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcIsoCountryCode_value" ON "AgInternedIptcIsoCountryCode" (
	"value"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcJobIdentifier_searchIndex" ON "AgInternedIptcJobIdentifier" (
	"searchIndex"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcJobIdentifier_value" ON "AgInternedIptcJobIdentifier" (
	"value"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcLocation_searchIndex" ON "AgInternedIptcLocation" (
	"searchIndex"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcLocation_value" ON "AgInternedIptcLocation" (
	"value"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcState_searchIndex" ON "AgInternedIptcState" (
	"searchIndex"
);
CREATE INDEX IF NOT EXISTS "index_AgInternedIptcState_value" ON "AgInternedIptcState" (
	"value"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionChangeCounter_changeCounter" ON "AgLibraryCollectionChangeCounter" (
	"changeCounter",
	"collection"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionContent_collection" ON "AgLibraryCollectionContent" (
	"collection"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionContent_owningModule" ON "AgLibraryCollectionContent" (
	"owningModule"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionImageChangeCounter_changeCounter" ON "AgLibraryCollectionImageChangeCounter" (
	"changeCounter",
	"collectionImage",
	"collection",
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionImageOzAlbumAssetIds_collectionAlbumAssetsLookup" ON "AgLibraryCollectionImageOzAlbumAssetIds" (
	"collection",
	"ozCatalogId"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionImageOzAlbumAssetIds_collectionFromAlbumAssetIdLookup" ON "AgLibraryCollectionImageOzAlbumAssetIds" (
	"ozAlbumAssetId",
	"ozCatalogId",
	"collectionImage",
	"collection",
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionImageOzAlbumAssetIds_imageAlbumAssetsLookup" ON "AgLibraryCollectionImageOzAlbumAssetIds" (
	"image",
	"ozCatalogId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryCollectionImageOzAlbumAssetIds_primaryKey" ON "AgLibraryCollectionImageOzAlbumAssetIds" (
	"collectionImage",
	"ozCatalogId",
	"collection",
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionImage_collection" ON "AgLibraryCollectionImage" (
	"collection"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionImage_imageCollection" ON "AgLibraryCollectionImage" (
	"image",
	"collection"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryCollectionLabel_collectionLabelIndex" ON "AgLibraryCollectionLabel" (
	"collection",
	"label"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionLabel_collectiondex" ON "AgLibraryCollectionLabel" (
	"collection"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionLabel_labelIndex" ON "AgLibraryCollectionLabel" (
	"label"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionOzAlbumIds_catalogAlbumsLookup" ON "AgLibraryCollectionOzAlbumIds" (
	"ozCatalogId",
	"ozAlbumId",
	"collection"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionOzAlbumIds_collectionFromAlbumIdLookup" ON "AgLibraryCollectionOzAlbumIds" (
	"ozAlbumId",
	"ozCatalogId",
	"collection"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryCollectionOzAlbumIds_primaryKey" ON "AgLibraryCollectionOzAlbumIds" (
	"collection",
	"ozCatalogId"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionStackData" ON "AgLibraryCollectionStackData" (
	"stack",
	"collection",
	"stackCount",
	"stackParent"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionStackImage_getStackFromImage" ON "AgLibraryCollectionStackImage" (
	"collection",
	"image",
	"stack",
	"position",
	"collapsed"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionStackImage_image" ON "AgLibraryCollectionStackImage" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionStackImage_orderByCollapseThenStackThenPosition" ON "AgLibraryCollectionStackImage" (
	"collection",
	"collapsed",
	"stack",
	"position",
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionStackImage_orderByPositionThenStack" ON "AgLibraryCollectionStackImage" (
	"collection",
	"position",
	"stack",
	"image",
	"collapsed"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionStackImage_orderByStackThenPosition" ON "AgLibraryCollectionStackImage" (
	"collection",
	"stack",
	"position",
	"image",
	"collapsed"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionStackImage_stack" ON "AgLibraryCollectionStackImage" (
	"stack"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionStack_stacksForCollection" ON "AgLibraryCollectionStack" (
	"collection",
	"collapsed"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryCollectionSyncedAlbumData_primaryKey" ON "AgLibraryCollectionSyncedAlbumData" (
	"collection",
	"payloadKey"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollectionTrackedAssets_byOzCatalogId" ON "AgLibraryCollectionTrackedAssets" (
	"ozCatalogId",
	"collection"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryCollectionTrackedAssets_primaryKey" ON "AgLibraryCollectionTrackedAssets" (
	"collection",
	"ozCatalogId"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollection_genealogy" ON "AgLibraryCollection" (
	"genealogy"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryCollection_parentAndName" ON "AgLibraryCollection" (
	"parent",
	"name"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFaceCluster_keyFace" ON "AgLibraryFaceCluster" (
	"keyFace"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFaceData_face" ON "AgLibraryFaceData" (
	"face"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFace_cluster" ON "AgLibraryFace" (
	"cluster"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFace_image" ON "AgLibraryFace" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFileAssetMetadata_sha256ToFileId" ON "AgLibraryFileAssetMetadata" (
	"sha256",
	"fileSize"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFile_folder" ON "AgLibraryFile" (
	"folder"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFile_importHash" ON "AgLibraryFile" (
	"importHash"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryFile_nameAndFolder" ON "AgLibraryFile" (
	"lc_idx_filename",
	"folder"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFolderFavorite_favoriteIndex" ON "AgLibraryFolderFavorite" (
	"favorite"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryFolderFavorite_folderFavoriteIndex" ON "AgLibraryFolderFavorite" (
	"folder",
	"favorite"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFolderFavorite_folderIndex" ON "AgLibraryFolderFavorite" (
	"folder"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryFolderLabel_folderLabelIndex" ON "AgLibraryFolderLabel" (
	"folder",
	"label"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFolderLabel_folderdex" ON "AgLibraryFolderLabel" (
	"folder"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFolderLabel_labelIndex" ON "AgLibraryFolderLabel" (
	"label"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFolderStackData" ON "AgLibraryFolderStackData" (
	"stack",
	"stackCount",
	"stackParent"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFolderStackImage_getStackFromImage" ON "AgLibraryFolderStackImage" (
	"image",
	"stack",
	"position",
	"collapsed"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFolderStackImage_orderByCollapseThenStackThenPosition" ON "AgLibraryFolderStackImage" (
	"collapsed",
	"stack",
	"position",
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFolderStackImage_orderByPositionThenStack" ON "AgLibraryFolderStackImage" (
	"position",
	"stack",
	"image",
	"collapsed"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFolderStackImage_orderByStackThenPosition" ON "AgLibraryFolderStackImage" (
	"stack",
	"position",
	"image",
	"collapsed"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFolderStack_collapsed" ON "AgLibraryFolderStack" (
	"collapsed"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryFolder_parentId" ON "AgLibraryFolder" (
	"parentId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryFolder_rootFolderAndPath" ON "AgLibraryFolder" (
	"rootFolder",
	"pathFromRoot"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryIPTC_image" ON "AgLibraryIPTC" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryImageAttributes_image" ON "AgLibraryImageAttributes" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryImageChangeCounter_changeCounter" ON "AgLibraryImageChangeCounter" (
	"changeCounter",
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryImageOzAssetIds_imageFromAssetIdLookup" ON "AgLibraryImageOzAssetIds" (
	"id_local",
	"ozAssetId",
	"ozCatalogId",
	"image",
	"ownedByCatalog"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryImageOzAssetIds_primaryKey" ON "AgLibraryImageOzAssetIds" (
	"image",
	"ozCatalogId"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryImageSaveXMP_statusCluster" ON "AgLibraryImageSaveXMP" (
	"taskStatus",
	"whenPosted",
	"taskID"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryImageSaveXMP_taskIDCluster" ON "AgLibraryImageSaveXMP" (
	"taskID",
	"whenPosted",
	"taskStatus"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryImageSearchData_image" ON "AgLibraryImageSearchData" (
	"image"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryImageSyncedAssetData_primaryKey" ON "AgLibraryImageSyncedAssetData" (
	"image",
	"payloadKey"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryImageXMPUpdater_statusCluster" ON "AgLibraryImageXMPUpdater" (
	"taskStatus",
	"whenPosted",
	"taskID"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryImageXMPUpdater_taskIDCluster" ON "AgLibraryImageXMPUpdater" (
	"taskID",
	"whenPosted",
	"taskStatus"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryImportImage_imageAndImport" ON "AgLibraryImportImage" (
	"image",
	"import"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryImportImage_import" ON "AgLibraryImportImage" (
	"import"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryKeywordCooccurrence_tag1Search" ON "AgLibraryKeywordCooccurrence" (
	"tag1",
	"value",
	"tag2"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryKeywordCooccurrence_tagsLookup" ON "AgLibraryKeywordCooccurrence" (
	"tag1",
	"tag2"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryKeywordCooccurrence_valueIndex" ON "AgLibraryKeywordCooccurrence" (
	"value"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryKeywordFace_face" ON "AgLibraryKeywordFace" (
	"face"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryKeywordFace_tag" ON "AgLibraryKeywordFace" (
	"tag"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryKeywordImage_image" ON "AgLibraryKeywordImage" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryKeywordImage_tag" ON "AgLibraryKeywordImage" (
	"tag"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryKeywordPopularity_popularity" ON "AgLibraryKeywordPopularity" (
	"popularity"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryKeywordSynonym_keyword" ON "AgLibraryKeywordSynonym" (
	"keyword"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryKeywordSynonym_lc_name" ON "AgLibraryKeywordSynonym" (
	"lc_name"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryKeyword_genealogy" ON "AgLibraryKeyword" (
	"genealogy"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryKeyword_parentAndLcName" ON "AgLibraryKeyword" (
	"parent",
	"lc_name"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryOzCommentIds_byAsset" ON "AgLibraryOzCommentIds" (
	"ozCatalogId",
	"ozSpaceId",
	"ozAssetId"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryOzCommentIds_bySpace" ON "AgLibraryOzCommentIds" (
	"ozCatalogId",
	"ozSpaceId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryOzCommentIds_primaryKey" ON "AgLibraryOzCommentIds" (
	"ozCatalogId",
	"ozCommentId"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryOzFavoriteIds_byAsset" ON "AgLibraryOzFavoriteIds" (
	"ozCatalogId",
	"ozSpaceId",
	"ozAssetId"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryOzFavoriteIds_bySpace" ON "AgLibraryOzFavoriteIds" (
	"ozCatalogId",
	"ozSpaceId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryOzFavoriteIds_primaryKey" ON "AgLibraryOzFavoriteIds" (
	"ozCatalogId",
	"ozFavoriteId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryOzFeedbackInfo_assetAndSpaceAndCatalog" ON "AgLibraryOzFeedbackInfo" (
	"ozAssetId",
	"ozSpaceId",
	"ozCatalogId"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryOzFeedbackInfo_lastFeedbackTime" ON "AgLibraryOzFeedbackInfo" (
	"lastFeedbackTime"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryPublishedCollectionContent_collection" ON "AgLibraryPublishedCollectionContent" (
	"collection"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryPublishedCollectionContent_owningModule" ON "AgLibraryPublishedCollectionContent" (
	"owningModule"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryPublishedCollectionImage_collection" ON "AgLibraryPublishedCollectionImage" (
	"collection"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryPublishedCollectionImage_imageCollection" ON "AgLibraryPublishedCollectionImage" (
	"image",
	"collection"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgLibraryPublishedCollectionLabel_collectionLabelIndex" ON "AgLibraryPublishedCollectionLabel" (
	"collection",
	"label"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryPublishedCollectionLabel_collectiondex" ON "AgLibraryPublishedCollectionLabel" (
	"collection"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryPublishedCollectionLabel_labelIndex" ON "AgLibraryPublishedCollectionLabel" (
	"label"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryPublishedCollection_genealogy" ON "AgLibraryPublishedCollection" (
	"genealogy"
);
CREATE INDEX IF NOT EXISTS "index_AgLibraryPublishedCollection_parentAndName" ON "AgLibraryPublishedCollection" (
	"parent",
	"name"
);
CREATE INDEX IF NOT EXISTS "index_AgMRULists_listID" ON "AgMRULists" (
	"listID"
);
CREATE INDEX IF NOT EXISTS "index_AgMetadataSearchIndex_image" ON "AgMetadataSearchIndex" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgOutputImageAsset_findByCollectionGroupByImage" ON "AgOutputImageAsset" (
	"moduleId",
	"collection",
	"image",
	"assetId"
);
CREATE INDEX IF NOT EXISTS "index_AgOutputImageAsset_findByCollectionImage" ON "AgOutputImageAsset" (
	"collection",
	"image",
	"moduleId",
	"assetId"
);
CREATE INDEX IF NOT EXISTS "index_AgOutputImageAsset_image" ON "AgOutputImageAsset" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgOzAuxBinaryMetadata_byAsset" ON "AgOzAuxBinaryMetadata" (
	"ozAssetId"
);
CREATE INDEX IF NOT EXISTS "index_AgOzCorruptedAuxIds_byAsset" ON "AgOzCorruptedAuxIds" (
	"ozAssetId"
);
CREATE INDEX IF NOT EXISTS "index_AgOzSpaceAlbumIds_byAlbumId" ON "AgOzSpaceAlbumIds" (
	"ozAlbumId",
	"ozCatalogId"
);
CREATE INDEX IF NOT EXISTS "index_AgOzSpaceAlbumIds_bySpaceId" ON "AgOzSpaceAlbumIds" (
	"ozSpaceId",
	"ozCatalogId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgOzSpaceAlbumIds_primaryKey" ON "AgOzSpaceAlbumIds" (
	"ozSpaceAlbumId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgOzSpaceIds_primaryKey" ON "AgOzSpaceIds" (
	"ozCatalogId",
	"ozSpaceId"
);
CREATE INDEX IF NOT EXISTS "index_AgPendingOzAlbumAssetIds_byAlbumAssetId" ON "AgPendingOzAlbumAssetIds" (
	"ozAlbumAssetId",
	"ozAssetId",
	"ozCatalogId",
	"ozAlbumId"
);
CREATE INDEX IF NOT EXISTS "index_AgPendingOzAlbumAssetIds_byAlbumId" ON "AgPendingOzAlbumAssetIds" (
	"ozAlbumId",
	"ozCatalogId",
	"ozAlbumAssetId",
	"ozAssetId"
);
CREATE INDEX IF NOT EXISTS "index_AgPendingOzAlbumAssetIds_byAssetId" ON "AgPendingOzAlbumAssetIds" (
	"ozAssetId",
	"ozCatalogId",
	"ozAlbumAssetId",
	"ozAlbumId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgPendingOzAlbumAssetIds_primaryKey" ON "AgPendingOzAlbumAssetIds" (
	"ozCatalogId",
	"ozAlbumAssetId",
	"ozAssetId",
	"ozAlbumId"
);
CREATE INDEX IF NOT EXISTS "index_AgPendingOzAssetBinaryDownloads_catalogIdOrdering" ON "AgPendingOzAssetBinaryDownloads" (
	"ozCatalogId",
	"whenQueued",
	"state",
	"ozAssetId",
	"path"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgPendingOzAssetBinaryDownloads_primaryKey" ON "AgPendingOzAssetBinaryDownloads" (
	"ozAssetId",
	"ozCatalogId"
);
CREATE INDEX IF NOT EXISTS "index_AgPendingOzAssetBinaryDownloads_stateSearches" ON "AgPendingOzAssetBinaryDownloads" (
	"state",
	"ozCatalogId",
	"whenQueued",
	"ozAssetId"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgPendingOzAssets_primaryKey" ON "AgPendingOzAssets" (
	"ozAssetId",
	"ozCatalogId"
);
CREATE INDEX IF NOT EXISTS "index_AgPendingOzAssets_stateSearches" ON "AgPendingOzAssets" (
	"state",
	"ozCatalogId",
	"ozAssetId"
);
CREATE INDEX IF NOT EXISTS "index_AgPhotoComment_photo" ON "AgPhotoComment" (
	"photo"
);
CREATE INDEX IF NOT EXISTS "index_AgPhotoComment_remoteId" ON "AgPhotoComment" (
	"remoteId"
);
CREATE INDEX IF NOT EXISTS "index_AgPhotoComment_remotePhoto" ON "AgPhotoComment" (
	"remotePhoto"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgPhotoPropertyArrayElement_pluginKey" ON "AgPhotoPropertyArrayElement" (
	"photo",
	"propertySpec",
	"arrayIndex"
);
CREATE INDEX IF NOT EXISTS "index_AgPhotoPropertyArrayElement_propertySpec" ON "AgPhotoPropertyArrayElement" (
	"propertySpec"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgPhotoPropertySpec_pluginKey" ON "AgPhotoPropertySpec" (
	"sourcePlugin",
	"key",
	"pluginVersion"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgPhotoProperty_pluginKey" ON "AgPhotoProperty" (
	"photo",
	"propertySpec"
);
CREATE INDEX IF NOT EXISTS "index_AgPhotoProperty_propertySpec" ON "AgPhotoProperty" (
	"propertySpec"
);
CREATE INDEX IF NOT EXISTS "index_AgPublishListenerWorklist_statusCluster" ON "AgPublishListenerWorklist" (
	"taskStatus",
	"whenPosted",
	"taskID"
);
CREATE INDEX IF NOT EXISTS "index_AgPublishListenerWorklist_taskIDCluster" ON "AgPublishListenerWorklist" (
	"taskID",
	"whenPosted",
	"taskStatus"
);
CREATE INDEX IF NOT EXISTS "index_AgRemotePhoto_collectionNeedsUpdating" ON "AgRemotePhoto" (
	"collection",
	"photoNeedsUpdating"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgRemotePhoto_collectionPhoto" ON "AgRemotePhoto" (
	"collection",
	"photo"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgRemotePhoto_collectionRemoteId" ON "AgRemotePhoto" (
	"collection",
	"remoteId"
);
CREATE INDEX IF NOT EXISTS "index_AgRemotePhoto_photo" ON "AgRemotePhoto" (
	"photo"
);
CREATE INDEX IF NOT EXISTS "index_AgSearchablePhotoPropertyArrayElement_lc_idx_internalValue" ON "AgSearchablePhotoPropertyArrayElement" (
	"lc_idx_internalValue"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgSearchablePhotoPropertyArrayElement_pluginKey" ON "AgSearchablePhotoPropertyArrayElement" (
	"photo",
	"propertySpec",
	"arrayIndex"
);
CREATE INDEX IF NOT EXISTS "index_AgSearchablePhotoPropertyArrayElement_propertyValue" ON "AgSearchablePhotoPropertyArrayElement" (
	"propertySpec",
	"internalValue"
);
CREATE INDEX IF NOT EXISTS "index_AgSearchablePhotoPropertyArrayElement_propertyValue_lc" ON "AgSearchablePhotoPropertyArrayElement" (
	"propertySpec",
	"lc_idx_internalValue"
);
CREATE INDEX IF NOT EXISTS "index_AgSearchablePhotoProperty_lc_idx_internalValue" ON "AgSearchablePhotoProperty" (
	"lc_idx_internalValue"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgSearchablePhotoProperty_pluginKey" ON "AgSearchablePhotoProperty" (
	"photo",
	"propertySpec"
);
CREATE INDEX IF NOT EXISTS "index_AgSearchablePhotoProperty_propertyValue" ON "AgSearchablePhotoProperty" (
	"propertySpec",
	"internalValue"
);
CREATE INDEX IF NOT EXISTS "index_AgSearchablePhotoProperty_propertyValue_lc" ON "AgSearchablePhotoProperty" (
	"propertySpec",
	"lc_idx_internalValue"
);
CREATE INDEX IF NOT EXISTS "index_AgSourceColorProfileConstants_image" ON "AgSourceColorProfileConstants" (
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgSourceColorProfileConstants_imageSourceColorProfileName" ON "AgSourceColorProfileConstants" (
	"profileName",
	"image"
);
CREATE INDEX IF NOT EXISTS "index_AgSpecialSourceContent_owningModule" ON "AgSpecialSourceContent" (
	"owningModule"
);
CREATE UNIQUE INDEX IF NOT EXISTS "index_AgSpecialSourceContent_sourceModule" ON "AgSpecialSourceContent" (
	"source",
	"owningModule"
);
CREATE INDEX IF NOT EXISTS "index_AgVideoInfo_image" ON "AgVideoInfo" (
	"image"
);
CREATE TRIGGER AgLibraryCollectionStackData_delete
								AFTER DELETE ON AgLibraryCollectionStack
								FOR EACH ROW
								BEGIN
									DELETE FROM AgLibraryCollectionStackData WHERE stack = OLD.id_local AND collection = OLD.collection;
								END;
CREATE TRIGGER AgLibraryCollectionStackData_init
								AFTER INSERT ON AgLibraryCollectionStack
								FOR EACH ROW
								BEGIN
									INSERT INTO AgLibraryCollectionStackData( stack, collection ) VALUES( NEW.id_local, NEW.collection );
								END;
CREATE TRIGGER AgLibraryCollectionStackData_initStackData
	AFTER INSERT ON AgLibraryCollectionStackData
	FOR EACH ROW
	BEGIN
		UPDATE AgLibraryCollectionStackData
			SET stackCount = (
				SELECT COUNT( * ) FROM AgLibraryCollectionStackImage
				WHERE stack = NEW.stack AND collection = NEW.collection )
			WHERE stack = NEW.stack AND collection = NEW.collection;
		UPDATE AgLibraryCollectionStackData
			SET stackParent = (
				SELECT image FROM AgLibraryCollectionStackImage
				WHERE stack = NEW.stack AND collection = NEW.collection AND
				      position = 1 )
			WHERE stack = NEW.stack AND collection = NEW.collection;
	END;
CREATE TRIGGER AgLibraryCollectionStackImage_propagateStackParentOnAdd
								   AFTER INSERT ON AgLibraryCollectionStackImage
								   FOR EACH ROW WHEN NEW.position = 1
								   BEGIN
										UPDATE AgLibraryCollectionStackData
										SET stackParent = NEW.image
										WHERE stack = NEW.stack AND
										      collection = NEW.collection;
									END;
CREATE TRIGGER AgLibraryCollectionStackImage_propagateStackParentOnUpdate
								   AFTER UPDATE OF position ON AgLibraryCollectionStackImage
								   FOR EACH ROW WHEN NEW.position = 1
								   BEGIN
										UPDATE AgLibraryCollectionStackData
										SET stackParent = NEW.image
										WHERE stack = NEW.stack AND
										      collection = NEW.collection;
									END;
CREATE TRIGGER AgLibraryCollectionStackImage_updateCountOnAdd
								   AFTER INSERT ON AgLibraryCollectionStackImage
								   FOR EACH ROW
								   BEGIN
										UPDATE AgLibraryCollectionStackData
										SET stackCount = stackCount + 1
										WHERE stack = NEW.stack AND
										      collection = NEW.collection;
									END;
CREATE TRIGGER AgLibraryCollectionStackImage_updateCountOnDelete
								   AFTER DELETE ON AgLibraryCollectionStackImage
								   FOR EACH ROW
								   BEGIN
										UPDATE AgLibraryCollectionStackData
										SET stackCount = MAX( 0, stackCount - 1 )
										WHERE stack = OLD.stack AND
										      collection = OLD.collection;
									END;
CREATE TRIGGER AgLibraryCollectionStack_propagateCollapseState
								   AFTER UPDATE OF collapsed ON AgLibraryCollectionStack
								   FOR EACH ROW
								   BEGIN
										UPDATE AgLibraryCollectionStackImage
										SET collapsed = NEW.collapsed
										WHERE AgLibraryCollectionStackImage.stack = NEW.id_local;
									END;
CREATE TRIGGER AgLibraryFolderStackData_delete
								AFTER DELETE ON AgLibraryFolderStack
								FOR EACH ROW
								BEGIN
									DELETE FROM AgLibraryFolderStackData WHERE stack = OLD.id_local;
								END;
CREATE TRIGGER AgLibraryFolderStackData_init
								AFTER INSERT ON AgLibraryFolderStack
								FOR EACH ROW
								BEGIN
									INSERT INTO AgLibraryFolderStackData( stack ) VALUES( NEW.id_local );
								END;
CREATE TRIGGER AgLibraryFolderStackData_initStackData
	AFTER INSERT ON AgLibraryFolderStackData
	FOR EACH ROW
	BEGIN
		UPDATE AgLibraryFolderStackData
			SET stackCount = (
				SELECT COUNT( * ) FROM AgLibraryFolderStackImage
				WHERE stack = NEW.stack )
			WHERE stack = NEW.stack;
		UPDATE AgLibraryFolderStackData
			SET stackParent = (
				SELECT image FROM AgLibraryFolderStackImage
				WHERE stack = NEW.stack AND position = 1 )
			WHERE stack = NEW.stack;

	END;
CREATE TRIGGER AgLibraryFolderStackImage_propagateStackParentOnAdd
								   AFTER INSERT ON AgLibraryFolderStackImage
								   FOR EACH ROW WHEN NEW.position = 1
								   BEGIN
										UPDATE AgLibraryFolderStackData
										SET stackParent = NEW.image
										WHERE stack = NEW.stack;
									END;
CREATE TRIGGER AgLibraryFolderStackImage_propagateStackParentOnUpdate
								   AFTER UPDATE OF position ON AgLibraryFolderStackImage
								   FOR EACH ROW WHEN NEW.position = 1
								   BEGIN
										UPDATE AgLibraryFolderStackData
										SET stackParent = NEW.image
										WHERE stack = NEW.stack;
									END;
CREATE TRIGGER AgLibraryFolderStackImage_updateCountOnAdd
								   AFTER INSERT ON AgLibraryFolderStackImage
								   FOR EACH ROW
								   BEGIN
										UPDATE AgLibraryFolderStackData
										SET stackCount = stackCount + 1
										WHERE stack = NEW.stack;
									END;
CREATE TRIGGER AgLibraryFolderStackImage_updateStackCountOnDelete
								   AFTER DELETE ON AgLibraryFolderStackImage
								   FOR EACH ROW
								   BEGIN
										UPDATE AgLibraryFolderStackData
										SET stackCount = MAX( 0, stackCount - 1 )
										WHERE stack = OLD.stack;
									END;
CREATE TRIGGER AgLibraryFolderStack_propagateCollapseState
								   AFTER UPDATE OF collapsed ON AgLibraryFolderStack
								   FOR EACH ROW
								   BEGIN
										UPDATE AgLibraryFolderStackImage
										SET collapsed = NEW.collapsed
										WHERE AgLibraryFolderStackImage.stack = NEW.id_local;
									END;
CREATE TRIGGER trigger_AgDNGProxyInfo_fileDeleted
											AFTER DELETE ON AgLibraryFile
											FOR EACH ROW
											BEGIN
												UPDATE AgDNGProxyInfo
												SET status = 'D', statusDateTime = datetime( 'now' )
												WHERE fileUUID = OLD.id_global;
											END;
CREATE TRIGGER trigger_AgDNGProxyInfo_fileInserted
						   					 AFTER INSERT ON AgLibraryFile
											 FOR EACH ROW
											 BEGIN
												UPDATE AgDNGProxyInfo
												SET status = 'U', statusDateTime = datetime( 'now' )
												WHERE fileUUID = NEW.id_global;
											END;
CREATE TRIGGER trigger_AgLibraryCollectionCoverImage_delete_collection
	AFTER DELETE on AgLibraryCollection
	FOR EACH ROW
	BEGIN
		DELETE FROM AgLibraryCollectionCoverImage
		WHERE collection = OLD.id_local;
	END;
CREATE TRIGGER trigger_AgLibraryCollectionCoverImage_delete_collectionImage
	AFTER DELETE on AgLibraryCollectionImage
	FOR EACH ROW
	BEGIN
		DELETE FROM AgLibraryCollectionCoverImage
		WHERE collection = OLD.collection AND collectionImage = OLD.id_local;
	END;
COMMIT;
