import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ProxyType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SYSTEM: _ClassVar[ProxyType]
    NOPROXY: _ClassVar[ProxyType]
    HTTP: _ClassVar[ProxyType]
    SOCKS5: _ClassVar[ProxyType]

class QRCodeScanMessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SHOW_IMAGE: _ClassVar[QRCodeScanMessageType]
    SHOW_IMAGE_CONTENT: _ClassVar[QRCodeScanMessageType]
    CHANGE_STATUS: _ClassVar[QRCodeScanMessageType]
    CLOSE: _ClassVar[QRCodeScanMessageType]
    ERROR: _ClassVar[QRCodeScanMessageType]

class UpdateChannel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    Release: _ClassVar[UpdateChannel]
    Beta: _ClassVar[UpdateChannel]

class LogLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    Trace: _ClassVar[LogLevel]
    Debug: _ClassVar[LogLevel]
    Info: _ClassVar[LogLevel]
    Warn: _ClassVar[LogLevel]
    Error: _ClassVar[LogLevel]

class OfflineFileStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OFFLINE_INIT: _ClassVar[OfflineFileStatus]
    OFFLINE_DOWNLOADING: _ClassVar[OfflineFileStatus]
    OFFLINE_FINISHED: _ClassVar[OfflineFileStatus]
    OFFLINE_ERROR: _ClassVar[OfflineFileStatus]
    OFFLINE_UNKNOWN: _ClassVar[OfflineFileStatus]

class FileReplaceRule(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    Skip: _ClassVar[FileReplaceRule]
    Overwrite: _ClassVar[FileReplaceRule]
    KeepHistoryVersion: _ClassVar[FileReplaceRule]

class FileDeleteRule(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    Delete: _ClassVar[FileDeleteRule]
    Recycle: _ClassVar[FileDeleteRule]
    Keep: _ClassVar[FileDeleteRule]
    MoveToVersionHistory: _ClassVar[FileDeleteRule]

class FileCompletionRule(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    None: _ClassVar[FileCompletionRule]
    DeleteSource: _ClassVar[FileCompletionRule]
    DeleteSourceAndEmptyFolder: _ClassVar[FileCompletionRule]
SYSTEM: ProxyType
NOPROXY: ProxyType
HTTP: ProxyType
SOCKS5: ProxyType
SHOW_IMAGE: QRCodeScanMessageType
SHOW_IMAGE_CONTENT: QRCodeScanMessageType
CHANGE_STATUS: QRCodeScanMessageType
CLOSE: QRCodeScanMessageType
ERROR: QRCodeScanMessageType
Release: UpdateChannel
Beta: UpdateChannel
Trace: LogLevel
Debug: LogLevel
Info: LogLevel
Warn: LogLevel
Error: LogLevel
OFFLINE_INIT: OfflineFileStatus
OFFLINE_DOWNLOADING: OfflineFileStatus
OFFLINE_FINISHED: OfflineFileStatus
OFFLINE_ERROR: OfflineFileStatus
OFFLINE_UNKNOWN: OfflineFileStatus
Skip: FileReplaceRule
Overwrite: FileReplaceRule
KeepHistoryVersion: FileReplaceRule
Delete: FileDeleteRule
Recycle: FileDeleteRule
Keep: FileDeleteRule
MoveToVersionHistory: FileDeleteRule
None: FileCompletionRule
DeleteSource: FileCompletionRule
DeleteSourceAndEmptyFolder: FileCompletionRule
VERSION_FIELD_NUMBER: _ClassVar[int]
version: _descriptor.FieldDescriptor

class GetTokenRequest(_message.Message):
    __slots__ = ("userName", "password")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    userName: str
    password: str
    def __init__(self, userName: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class JWTToken(_message.Message):
    __slots__ = ("success", "errorMessage", "token", "expiration")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRATION_FIELD_NUMBER: _ClassVar[int]
    success: bool
    errorMessage: str
    token: str
    expiration: _timestamp_pb2.Timestamp
    def __init__(self, success: bool = ..., errorMessage: _Optional[str] = ..., token: _Optional[str] = ..., expiration: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class FileRequest(_message.Message):
    __slots__ = ("path", "forceRefresh")
    PATH_FIELD_NUMBER: _ClassVar[int]
    FORCEREFRESH_FIELD_NUMBER: _ClassVar[int]
    path: str
    forceRefresh: bool
    def __init__(self, path: _Optional[str] = ..., forceRefresh: bool = ...) -> None: ...

class MultiFileRequest(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, path: _Optional[_Iterable[str]] = ...) -> None: ...

class FileOperationResult(_message.Message):
    __slots__ = ("success", "errorMessage", "resultFilePaths")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    RESULTFILEPATHS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    errorMessage: str
    resultFilePaths: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, success: bool = ..., errorMessage: _Optional[str] = ..., resultFilePaths: _Optional[_Iterable[str]] = ...) -> None: ...

class StringResult(_message.Message):
    __slots__ = ("result",)
    RESULT_FIELD_NUMBER: _ClassVar[int]
    result: str
    def __init__(self, result: _Optional[str] = ...) -> None: ...

class GetDownloadUrlPathRequest(_message.Message):
    __slots__ = ("path", "preview", "lazy_read")
    PATH_FIELD_NUMBER: _ClassVar[int]
    PREVIEW_FIELD_NUMBER: _ClassVar[int]
    LAZY_READ_FIELD_NUMBER: _ClassVar[int]
    path: str
    preview: bool
    lazy_read: bool
    def __init__(self, path: _Optional[str] = ..., preview: bool = ..., lazy_read: bool = ...) -> None: ...

class DownloadUrlPathInfo(_message.Message):
    __slots__ = ("downloadUrlPath", "expiresIn", "directUrl")
    DOWNLOADURLPATH_FIELD_NUMBER: _ClassVar[int]
    EXPIRESIN_FIELD_NUMBER: _ClassVar[int]
    DIRECTURL_FIELD_NUMBER: _ClassVar[int]
    downloadUrlPath: str
    expiresIn: int
    directUrl: str
    def __init__(self, downloadUrlPath: _Optional[str] = ..., expiresIn: _Optional[int] = ..., directUrl: _Optional[str] = ...) -> None: ...

class BoolResult(_message.Message):
    __slots__ = ("result",)
    RESULT_FIELD_NUMBER: _ClassVar[int]
    result: bool
    def __init__(self, result: bool = ...) -> None: ...

class UnmountArchiveResult(_message.Message):
    __slots__ = ("result",)
    RESULT_FIELD_NUMBER: _ClassVar[int]
    result: str
    def __init__(self, result: _Optional[str] = ...) -> None: ...

class ListSubFileRequest(_message.Message):
    __slots__ = ("path", "forceRefresh", "checkExpires")
    PATH_FIELD_NUMBER: _ClassVar[int]
    FORCEREFRESH_FIELD_NUMBER: _ClassVar[int]
    CHECKEXPIRES_FIELD_NUMBER: _ClassVar[int]
    path: str
    forceRefresh: bool
    checkExpires: bool
    def __init__(self, path: _Optional[str] = ..., forceRefresh: bool = ..., checkExpires: bool = ...) -> None: ...

class SearchRequest(_message.Message):
    __slots__ = ("path", "searchFor", "forceRefresh", "fuzzyMatch")
    PATH_FIELD_NUMBER: _ClassVar[int]
    SEARCHFOR_FIELD_NUMBER: _ClassVar[int]
    FORCEREFRESH_FIELD_NUMBER: _ClassVar[int]
    FUZZYMATCH_FIELD_NUMBER: _ClassVar[int]
    path: str
    searchFor: str
    forceRefresh: bool
    fuzzyMatch: bool
    def __init__(self, path: _Optional[str] = ..., searchFor: _Optional[str] = ..., forceRefresh: bool = ..., fuzzyMatch: bool = ...) -> None: ...

class AddOfflineFileRequest(_message.Message):
    __slots__ = ("urls", "toFolder")
    URLS_FIELD_NUMBER: _ClassVar[int]
    TOFOLDER_FIELD_NUMBER: _ClassVar[int]
    urls: str
    toFolder: str
    def __init__(self, urls: _Optional[str] = ..., toFolder: _Optional[str] = ...) -> None: ...

class RemoveOfflineFilesRequest(_message.Message):
    __slots__ = ("cloudName", "cloudAccountId", "deleteFiles", "infoHashes", "path")
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    CLOUDACCOUNTID_FIELD_NUMBER: _ClassVar[int]
    DELETEFILES_FIELD_NUMBER: _ClassVar[int]
    INFOHASHES_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    cloudName: str
    cloudAccountId: str
    deleteFiles: bool
    infoHashes: _containers.RepeatedScalarFieldContainer[str]
    path: str
    def __init__(self, cloudName: _Optional[str] = ..., cloudAccountId: _Optional[str] = ..., deleteFiles: bool = ..., infoHashes: _Optional[_Iterable[str]] = ..., path: _Optional[str] = ...) -> None: ...

class AddSharedLinkRequest(_message.Message):
    __slots__ = ("sharedLinkUrl", "sharedPassword", "toFolder")
    SHAREDLINKURL_FIELD_NUMBER: _ClassVar[int]
    SHAREDPASSWORD_FIELD_NUMBER: _ClassVar[int]
    TOFOLDER_FIELD_NUMBER: _ClassVar[int]
    sharedLinkUrl: str
    sharedPassword: str
    toFolder: str
    def __init__(self, sharedLinkUrl: _Optional[str] = ..., sharedPassword: _Optional[str] = ..., toFolder: _Optional[str] = ...) -> None: ...

class SubFilesReply(_message.Message):
    __slots__ = ("subFiles",)
    SUBFILES_FIELD_NUMBER: _ClassVar[int]
    subFiles: _containers.RepeatedCompositeFieldContainer[CloudDriveFile]
    def __init__(self, subFiles: _Optional[_Iterable[_Union[CloudDriveFile, _Mapping]]] = ...) -> None: ...

class FindFileByPathRequest(_message.Message):
    __slots__ = ("parentPath", "path")
    PARENTPATH_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    parentPath: str
    path: str
    def __init__(self, parentPath: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class CreateFolderRequest(_message.Message):
    __slots__ = ("parentPath", "folderName")
    PARENTPATH_FIELD_NUMBER: _ClassVar[int]
    FOLDERNAME_FIELD_NUMBER: _ClassVar[int]
    parentPath: str
    folderName: str
    def __init__(self, parentPath: _Optional[str] = ..., folderName: _Optional[str] = ...) -> None: ...

class CreateEncryptedFolderRequest(_message.Message):
    __slots__ = ("parentPath", "folderName", "password", "savePassword")
    PARENTPATH_FIELD_NUMBER: _ClassVar[int]
    FOLDERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    SAVEPASSWORD_FIELD_NUMBER: _ClassVar[int]
    parentPath: str
    folderName: str
    password: str
    savePassword: bool
    def __init__(self, parentPath: _Optional[str] = ..., folderName: _Optional[str] = ..., password: _Optional[str] = ..., savePassword: bool = ...) -> None: ...

class UnlockEncryptedFileRequest(_message.Message):
    __slots__ = ("path", "password", "permanentUnlock")
    PATH_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    PERMANENTUNLOCK_FIELD_NUMBER: _ClassVar[int]
    path: str
    password: str
    permanentUnlock: bool
    def __init__(self, path: _Optional[str] = ..., password: _Optional[str] = ..., permanentUnlock: bool = ...) -> None: ...

class CreateFolderResult(_message.Message):
    __slots__ = ("folderCreated", "result")
    FOLDERCREATED_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    folderCreated: CloudDriveFile
    result: FileOperationResult
    def __init__(self, folderCreated: _Optional[_Union[CloudDriveFile, _Mapping]] = ..., result: _Optional[_Union[FileOperationResult, _Mapping]] = ...) -> None: ...

class CreateFileRequest(_message.Message):
    __slots__ = ("parentPath", "fileName")
    PARENTPATH_FIELD_NUMBER: _ClassVar[int]
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    parentPath: str
    fileName: str
    def __init__(self, parentPath: _Optional[str] = ..., fileName: _Optional[str] = ...) -> None: ...

class CreateFileResult(_message.Message):
    __slots__ = ("fileHandle",)
    FILEHANDLE_FIELD_NUMBER: _ClassVar[int]
    fileHandle: int
    def __init__(self, fileHandle: _Optional[int] = ...) -> None: ...

class CloseFileRequest(_message.Message):
    __slots__ = ("fileHandle",)
    FILEHANDLE_FIELD_NUMBER: _ClassVar[int]
    fileHandle: int
    def __init__(self, fileHandle: _Optional[int] = ...) -> None: ...

class MoveFileRequest(_message.Message):
    __slots__ = ("theFilePaths", "destPath", "conflictPolicy", "moveAcrossClouds", "handleConflictRecursively")
    class ConflictPolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Overwrite: _ClassVar[MoveFileRequest.ConflictPolicy]
        Rename: _ClassVar[MoveFileRequest.ConflictPolicy]
        Skip: _ClassVar[MoveFileRequest.ConflictPolicy]
    Overwrite: MoveFileRequest.ConflictPolicy
    Rename: MoveFileRequest.ConflictPolicy
    Skip: MoveFileRequest.ConflictPolicy
    THEFILEPATHS_FIELD_NUMBER: _ClassVar[int]
    DESTPATH_FIELD_NUMBER: _ClassVar[int]
    CONFLICTPOLICY_FIELD_NUMBER: _ClassVar[int]
    MOVEACROSSCLOUDS_FIELD_NUMBER: _ClassVar[int]
    HANDLECONFLICTRECURSIVELY_FIELD_NUMBER: _ClassVar[int]
    theFilePaths: _containers.RepeatedScalarFieldContainer[str]
    destPath: str
    conflictPolicy: MoveFileRequest.ConflictPolicy
    moveAcrossClouds: bool
    handleConflictRecursively: bool
    def __init__(self, theFilePaths: _Optional[_Iterable[str]] = ..., destPath: _Optional[str] = ..., conflictPolicy: _Optional[_Union[MoveFileRequest.ConflictPolicy, str]] = ..., moveAcrossClouds: bool = ..., handleConflictRecursively: bool = ...) -> None: ...

class CopyFileRequest(_message.Message):
    __slots__ = ("theFilePaths", "destPath", "conflictPolicy", "handleConflictRecursively")
    class ConflictPolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Overwrite: _ClassVar[CopyFileRequest.ConflictPolicy]
        Rename: _ClassVar[CopyFileRequest.ConflictPolicy]
        Skip: _ClassVar[CopyFileRequest.ConflictPolicy]
    Overwrite: CopyFileRequest.ConflictPolicy
    Rename: CopyFileRequest.ConflictPolicy
    Skip: CopyFileRequest.ConflictPolicy
    THEFILEPATHS_FIELD_NUMBER: _ClassVar[int]
    DESTPATH_FIELD_NUMBER: _ClassVar[int]
    CONFLICTPOLICY_FIELD_NUMBER: _ClassVar[int]
    HANDLECONFLICTRECURSIVELY_FIELD_NUMBER: _ClassVar[int]
    theFilePaths: _containers.RepeatedScalarFieldContainer[str]
    destPath: str
    conflictPolicy: CopyFileRequest.ConflictPolicy
    handleConflictRecursively: bool
    def __init__(self, theFilePaths: _Optional[_Iterable[str]] = ..., destPath: _Optional[str] = ..., conflictPolicy: _Optional[_Union[CopyFileRequest.ConflictPolicy, str]] = ..., handleConflictRecursively: bool = ...) -> None: ...

class WriteFileRequest(_message.Message):
    __slots__ = ("fileHandle", "startPos", "length", "buffer", "closeFile")
    FILEHANDLE_FIELD_NUMBER: _ClassVar[int]
    STARTPOS_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    BUFFER_FIELD_NUMBER: _ClassVar[int]
    CLOSEFILE_FIELD_NUMBER: _ClassVar[int]
    fileHandle: int
    startPos: int
    length: int
    buffer: bytes
    closeFile: bool
    def __init__(self, fileHandle: _Optional[int] = ..., startPos: _Optional[int] = ..., length: _Optional[int] = ..., buffer: _Optional[bytes] = ..., closeFile: bool = ...) -> None: ...

class WriteFileResult(_message.Message):
    __slots__ = ("bytesWritten",)
    BYTESWRITTEN_FIELD_NUMBER: _ClassVar[int]
    bytesWritten: int
    def __init__(self, bytesWritten: _Optional[int] = ...) -> None: ...

class RenameFileRequest(_message.Message):
    __slots__ = ("theFilePath", "newName")
    THEFILEPATH_FIELD_NUMBER: _ClassVar[int]
    NEWNAME_FIELD_NUMBER: _ClassVar[int]
    theFilePath: str
    newName: str
    def __init__(self, theFilePath: _Optional[str] = ..., newName: _Optional[str] = ...) -> None: ...

class RenameFilesRequest(_message.Message):
    __slots__ = ("renameFiles",)
    RENAMEFILES_FIELD_NUMBER: _ClassVar[int]
    renameFiles: _containers.RepeatedCompositeFieldContainer[RenameFileRequest]
    def __init__(self, renameFiles: _Optional[_Iterable[_Union[RenameFileRequest, _Mapping]]] = ...) -> None: ...

class CloudDriveFile(_message.Message):
    __slots__ = ("id", "name", "fullPathName", "size", "fileType", "createTime", "writeTime", "accessTime", "CloudAPI", "thumbnailUrl", "previewUrl", "originalPath", "isDirectory", "isRoot", "isCloudRoot", "isCloudDirectory", "isCloudFile", "isSearchResult", "isForbidden", "isLocal", "canMount", "canUnmount", "canDirectAccessThumbnailURL", "canSearch", "hasDetailProperties", "detailProperties", "canOfflineDownload", "canAddShareLink", "dirCacheTimeToLiveSecs", "canDeletePermanently", "fileHashes", "fileEncryptionType", "CanCreateEncryptedFolder", "CanLock", "CanSyncFileChangesFromCloud", "supportOfflineDownloadManagement", "downloadUrlPath")
    class FileType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Directory: _ClassVar[CloudDriveFile.FileType]
        File: _ClassVar[CloudDriveFile.FileType]
        Other: _ClassVar[CloudDriveFile.FileType]
    Directory: CloudDriveFile.FileType
    File: CloudDriveFile.FileType
    Other: CloudDriveFile.FileType
    class HashType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Unknown: _ClassVar[CloudDriveFile.HashType]
        Md5: _ClassVar[CloudDriveFile.HashType]
        Sha1: _ClassVar[CloudDriveFile.HashType]
        PikPakSha1: _ClassVar[CloudDriveFile.HashType]
    Unknown: CloudDriveFile.HashType
    Md5: CloudDriveFile.HashType
    Sha1: CloudDriveFile.HashType
    PikPakSha1: CloudDriveFile.HashType
    class FileEncryptionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        None: _ClassVar[CloudDriveFile.FileEncryptionType]
        Encrypted: _ClassVar[CloudDriveFile.FileEncryptionType]
        Unlocked: _ClassVar[CloudDriveFile.FileEncryptionType]
    None: CloudDriveFile.FileEncryptionType
    Encrypted: CloudDriveFile.FileEncryptionType
    Unlocked: CloudDriveFile.FileEncryptionType
    class FileHashesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: str
        def __init__(self, key: _Optional[int] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    FULLPATHNAME_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    FILETYPE_FIELD_NUMBER: _ClassVar[int]
    CREATETIME_FIELD_NUMBER: _ClassVar[int]
    WRITETIME_FIELD_NUMBER: _ClassVar[int]
    ACCESSTIME_FIELD_NUMBER: _ClassVar[int]
    CLOUDAPI_FIELD_NUMBER: _ClassVar[int]
    THUMBNAILURL_FIELD_NUMBER: _ClassVar[int]
    PREVIEWURL_FIELD_NUMBER: _ClassVar[int]
    ORIGINALPATH_FIELD_NUMBER: _ClassVar[int]
    ISDIRECTORY_FIELD_NUMBER: _ClassVar[int]
    ISROOT_FIELD_NUMBER: _ClassVar[int]
    ISCLOUDROOT_FIELD_NUMBER: _ClassVar[int]
    ISCLOUDDIRECTORY_FIELD_NUMBER: _ClassVar[int]
    ISCLOUDFILE_FIELD_NUMBER: _ClassVar[int]
    ISSEARCHRESULT_FIELD_NUMBER: _ClassVar[int]
    ISFORBIDDEN_FIELD_NUMBER: _ClassVar[int]
    ISLOCAL_FIELD_NUMBER: _ClassVar[int]
    CANMOUNT_FIELD_NUMBER: _ClassVar[int]
    CANUNMOUNT_FIELD_NUMBER: _ClassVar[int]
    CANDIRECTACCESSTHUMBNAILURL_FIELD_NUMBER: _ClassVar[int]
    CANSEARCH_FIELD_NUMBER: _ClassVar[int]
    HASDETAILPROPERTIES_FIELD_NUMBER: _ClassVar[int]
    DETAILPROPERTIES_FIELD_NUMBER: _ClassVar[int]
    CANOFFLINEDOWNLOAD_FIELD_NUMBER: _ClassVar[int]
    CANADDSHARELINK_FIELD_NUMBER: _ClassVar[int]
    DIRCACHETIMETOLIVESECS_FIELD_NUMBER: _ClassVar[int]
    CANDELETEPERMANENTLY_FIELD_NUMBER: _ClassVar[int]
    FILEHASHES_FIELD_NUMBER: _ClassVar[int]
    FILEENCRYPTIONTYPE_FIELD_NUMBER: _ClassVar[int]
    CANCREATEENCRYPTEDFOLDER_FIELD_NUMBER: _ClassVar[int]
    CANLOCK_FIELD_NUMBER: _ClassVar[int]
    CANSYNCFILECHANGESFROMCLOUD_FIELD_NUMBER: _ClassVar[int]
    SUPPORTOFFLINEDOWNLOADMANAGEMENT_FIELD_NUMBER: _ClassVar[int]
    DOWNLOADURLPATH_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    fullPathName: str
    size: int
    fileType: CloudDriveFile.FileType
    createTime: _timestamp_pb2.Timestamp
    writeTime: _timestamp_pb2.Timestamp
    accessTime: _timestamp_pb2.Timestamp
    CloudAPI: CloudAPI
    thumbnailUrl: str
    previewUrl: str
    originalPath: str
    isDirectory: bool
    isRoot: bool
    isCloudRoot: bool
    isCloudDirectory: bool
    isCloudFile: bool
    isSearchResult: bool
    isForbidden: bool
    isLocal: bool
    canMount: bool
    canUnmount: bool
    canDirectAccessThumbnailURL: bool
    canSearch: bool
    hasDetailProperties: bool
    detailProperties: FileDetailProperties
    canOfflineDownload: bool
    canAddShareLink: bool
    dirCacheTimeToLiveSecs: int
    canDeletePermanently: bool
    fileHashes: _containers.ScalarMap[int, str]
    fileEncryptionType: CloudDriveFile.FileEncryptionType
    CanCreateEncryptedFolder: bool
    CanLock: bool
    CanSyncFileChangesFromCloud: bool
    supportOfflineDownloadManagement: bool
    downloadUrlPath: DownloadUrlPathInfo
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., fullPathName: _Optional[str] = ..., size: _Optional[int] = ..., fileType: _Optional[_Union[CloudDriveFile.FileType, str]] = ..., createTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., writeTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., accessTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., CloudAPI: _Optional[_Union[CloudAPI, _Mapping]] = ..., thumbnailUrl: _Optional[str] = ..., previewUrl: _Optional[str] = ..., originalPath: _Optional[str] = ..., isDirectory: bool = ..., isRoot: bool = ..., isCloudRoot: bool = ..., isCloudDirectory: bool = ..., isCloudFile: bool = ..., isSearchResult: bool = ..., isForbidden: bool = ..., isLocal: bool = ..., canMount: bool = ..., canUnmount: bool = ..., canDirectAccessThumbnailURL: bool = ..., canSearch: bool = ..., hasDetailProperties: bool = ..., detailProperties: _Optional[_Union[FileDetailProperties, _Mapping]] = ..., canOfflineDownload: bool = ..., canAddShareLink: bool = ..., dirCacheTimeToLiveSecs: _Optional[int] = ..., canDeletePermanently: bool = ..., fileHashes: _Optional[_Mapping[int, str]] = ..., fileEncryptionType: _Optional[_Union[CloudDriveFile.FileEncryptionType, str]] = ..., CanCreateEncryptedFolder: bool = ..., CanLock: bool = ..., CanSyncFileChangesFromCloud: bool = ..., supportOfflineDownloadManagement: bool = ..., downloadUrlPath: _Optional[_Union[DownloadUrlPathInfo, _Mapping]] = ...) -> None: ...

class SpaceInfo(_message.Message):
    __slots__ = ("totalSpace", "usedSpace", "freeSpace")
    TOTALSPACE_FIELD_NUMBER: _ClassVar[int]
    USEDSPACE_FIELD_NUMBER: _ClassVar[int]
    FREESPACE_FIELD_NUMBER: _ClassVar[int]
    totalSpace: int
    usedSpace: int
    freeSpace: int
    def __init__(self, totalSpace: _Optional[int] = ..., usedSpace: _Optional[int] = ..., freeSpace: _Optional[int] = ...) -> None: ...

class CloudAPI(_message.Message):
    __slots__ = ("name", "userName", "nickName", "isLocked", "supportMultiThreadUploading", "supportQpsLimit", "isCloudEventListenerRunning", "hasPromotions", "promotionTitle", "path")
    NAME_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    NICKNAME_FIELD_NUMBER: _ClassVar[int]
    ISLOCKED_FIELD_NUMBER: _ClassVar[int]
    SUPPORTMULTITHREADUPLOADING_FIELD_NUMBER: _ClassVar[int]
    SUPPORTQPSLIMIT_FIELD_NUMBER: _ClassVar[int]
    ISCLOUDEVENTLISTENERRUNNING_FIELD_NUMBER: _ClassVar[int]
    HASPROMOTIONS_FIELD_NUMBER: _ClassVar[int]
    PROMOTIONTITLE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    name: str
    userName: str
    nickName: str
    isLocked: bool
    supportMultiThreadUploading: bool
    supportQpsLimit: bool
    isCloudEventListenerRunning: bool
    hasPromotions: bool
    promotionTitle: str
    path: str
    def __init__(self, name: _Optional[str] = ..., userName: _Optional[str] = ..., nickName: _Optional[str] = ..., isLocked: bool = ..., supportMultiThreadUploading: bool = ..., supportQpsLimit: bool = ..., isCloudEventListenerRunning: bool = ..., hasPromotions: bool = ..., promotionTitle: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class CloudMembership(_message.Message):
    __slots__ = ("identity", "expireTime", "level")
    IDENTITY_FIELD_NUMBER: _ClassVar[int]
    EXPIRETIME_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    identity: str
    expireTime: _timestamp_pb2.Timestamp
    level: str
    def __init__(self, identity: _Optional[str] = ..., expireTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., level: _Optional[str] = ...) -> None: ...

class CloudMemberships(_message.Message):
    __slots__ = ("memberships",)
    MEMBERSHIPS_FIELD_NUMBER: _ClassVar[int]
    memberships: _containers.RepeatedCompositeFieldContainer[CloudMembership]
    def __init__(self, memberships: _Optional[_Iterable[_Union[CloudMembership, _Mapping]]] = ...) -> None: ...

class FileDetailProperties(_message.Message):
    __slots__ = ("totalFileCount", "totalFolderCount", "totalSize", "isFaved", "isShared", "originalPath")
    TOTALFILECOUNT_FIELD_NUMBER: _ClassVar[int]
    TOTALFOLDERCOUNT_FIELD_NUMBER: _ClassVar[int]
    TOTALSIZE_FIELD_NUMBER: _ClassVar[int]
    ISFAVED_FIELD_NUMBER: _ClassVar[int]
    ISSHARED_FIELD_NUMBER: _ClassVar[int]
    ORIGINALPATH_FIELD_NUMBER: _ClassVar[int]
    totalFileCount: int
    totalFolderCount: int
    totalSize: int
    isFaved: bool
    isShared: bool
    originalPath: str
    def __init__(self, totalFileCount: _Optional[int] = ..., totalFolderCount: _Optional[int] = ..., totalSize: _Optional[int] = ..., isFaved: bool = ..., isShared: bool = ..., originalPath: _Optional[str] = ...) -> None: ...

class FileMetaData(_message.Message):
    __slots__ = ("metadata",)
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    METADATA_FIELD_NUMBER: _ClassVar[int]
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class CloudDriveSystemInfo(_message.Message):
    __slots__ = ("IsLogin", "UserName", "SystemReady", "SystemMessage", "hasError")
    ISLOGIN_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    SYSTEMREADY_FIELD_NUMBER: _ClassVar[int]
    SYSTEMMESSAGE_FIELD_NUMBER: _ClassVar[int]
    HASERROR_FIELD_NUMBER: _ClassVar[int]
    IsLogin: bool
    UserName: str
    SystemReady: bool
    SystemMessage: str
    hasError: bool
    def __init__(self, IsLogin: bool = ..., UserName: _Optional[str] = ..., SystemReady: bool = ..., SystemMessage: _Optional[str] = ..., hasError: bool = ...) -> None: ...

class UserLoginRequest(_message.Message):
    __slots__ = ("userName", "password", "synDataToCloud")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    SYNDATATOCLOUD_FIELD_NUMBER: _ClassVar[int]
    userName: str
    password: str
    synDataToCloud: bool
    def __init__(self, userName: _Optional[str] = ..., password: _Optional[str] = ..., synDataToCloud: bool = ...) -> None: ...

class UserRegisterRequest(_message.Message):
    __slots__ = ("userName", "password")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    userName: str
    password: str
    def __init__(self, userName: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class UserLogoutRequest(_message.Message):
    __slots__ = ("logoutFromCloudFS",)
    LOGOUTFROMCLOUDFS_FIELD_NUMBER: _ClassVar[int]
    logoutFromCloudFS: bool
    def __init__(self, logoutFromCloudFS: bool = ...) -> None: ...

class ChangePasswordRequest(_message.Message):
    __slots__ = ("oldPassword", "newPassword")
    OLDPASSWORD_FIELD_NUMBER: _ClassVar[int]
    NEWPASSWORD_FIELD_NUMBER: _ClassVar[int]
    oldPassword: str
    newPassword: str
    def __init__(self, oldPassword: _Optional[str] = ..., newPassword: _Optional[str] = ...) -> None: ...

class AccountStatusResult(_message.Message):
    __slots__ = ("userName", "emailConfirmed", "accountBalance", "accountPlan", "accountRoles", "secondPlan", "partnerReferralCode", "trustedDevice", "userNameIsDeviceId")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    EMAILCONFIRMED_FIELD_NUMBER: _ClassVar[int]
    ACCOUNTBALANCE_FIELD_NUMBER: _ClassVar[int]
    ACCOUNTPLAN_FIELD_NUMBER: _ClassVar[int]
    ACCOUNTROLES_FIELD_NUMBER: _ClassVar[int]
    SECONDPLAN_FIELD_NUMBER: _ClassVar[int]
    PARTNERREFERRALCODE_FIELD_NUMBER: _ClassVar[int]
    TRUSTEDDEVICE_FIELD_NUMBER: _ClassVar[int]
    USERNAMEISDEVICEID_FIELD_NUMBER: _ClassVar[int]
    userName: str
    emailConfirmed: str
    accountBalance: float
    accountPlan: AccountPlan
    accountRoles: _containers.RepeatedCompositeFieldContainer[AccountRole]
    secondPlan: AccountPlan
    partnerReferralCode: str
    trustedDevice: bool
    userNameIsDeviceId: bool
    def __init__(self, userName: _Optional[str] = ..., emailConfirmed: _Optional[str] = ..., accountBalance: _Optional[float] = ..., accountPlan: _Optional[_Union[AccountPlan, _Mapping]] = ..., accountRoles: _Optional[_Iterable[_Union[AccountRole, _Mapping]]] = ..., secondPlan: _Optional[_Union[AccountPlan, _Mapping]] = ..., partnerReferralCode: _Optional[str] = ..., trustedDevice: bool = ..., userNameIsDeviceId: bool = ...) -> None: ...

class AccountPlan(_message.Message):
    __slots__ = ("planName", "description", "fontAwesomeIcon", "durationDescription", "endTime")
    PLANNAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    FONTAWESOMEICON_FIELD_NUMBER: _ClassVar[int]
    DURATIONDESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ENDTIME_FIELD_NUMBER: _ClassVar[int]
    planName: str
    description: str
    fontAwesomeIcon: str
    durationDescription: str
    endTime: _timestamp_pb2.Timestamp
    def __init__(self, planName: _Optional[str] = ..., description: _Optional[str] = ..., fontAwesomeIcon: _Optional[str] = ..., durationDescription: _Optional[str] = ..., endTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class AccountRole(_message.Message):
    __slots__ = ("roleName", "description", "value")
    ROLENAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    roleName: str
    description: str
    value: int
    def __init__(self, roleName: _Optional[str] = ..., description: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...

class RuntimeInfo(_message.Message):
    __slots__ = ("productName", "productVersion", "CloudAPIVersion", "osInfo")
    PRODUCTNAME_FIELD_NUMBER: _ClassVar[int]
    PRODUCTVERSION_FIELD_NUMBER: _ClassVar[int]
    CLOUDAPIVERSION_FIELD_NUMBER: _ClassVar[int]
    OSINFO_FIELD_NUMBER: _ClassVar[int]
    productName: str
    productVersion: str
    CloudAPIVersion: str
    osInfo: str
    def __init__(self, productName: _Optional[str] = ..., productVersion: _Optional[str] = ..., CloudAPIVersion: _Optional[str] = ..., osInfo: _Optional[str] = ...) -> None: ...

class RunInfo(_message.Message):
    __slots__ = ("cpuUsage", "memUsageKB", "uptime", "fhTableCount", "dirCacheCount", "tempFileCount", "dbDirCacheCount", "downloadBytesPerSecond", "uploadBytesPerSecond", "totalMemoryKB")
    CPUUSAGE_FIELD_NUMBER: _ClassVar[int]
    MEMUSAGEKB_FIELD_NUMBER: _ClassVar[int]
    UPTIME_FIELD_NUMBER: _ClassVar[int]
    FHTABLECOUNT_FIELD_NUMBER: _ClassVar[int]
    DIRCACHECOUNT_FIELD_NUMBER: _ClassVar[int]
    TEMPFILECOUNT_FIELD_NUMBER: _ClassVar[int]
    DBDIRCACHECOUNT_FIELD_NUMBER: _ClassVar[int]
    DOWNLOADBYTESPERSECOND_FIELD_NUMBER: _ClassVar[int]
    UPLOADBYTESPERSECOND_FIELD_NUMBER: _ClassVar[int]
    TOTALMEMORYKB_FIELD_NUMBER: _ClassVar[int]
    cpuUsage: float
    memUsageKB: int
    uptime: float
    fhTableCount: int
    dirCacheCount: int
    tempFileCount: int
    dbDirCacheCount: int
    downloadBytesPerSecond: float
    uploadBytesPerSecond: float
    totalMemoryKB: int
    def __init__(self, cpuUsage: _Optional[float] = ..., memUsageKB: _Optional[int] = ..., uptime: _Optional[float] = ..., fhTableCount: _Optional[int] = ..., dirCacheCount: _Optional[int] = ..., tempFileCount: _Optional[int] = ..., dbDirCacheCount: _Optional[int] = ..., downloadBytesPerSecond: _Optional[float] = ..., uploadBytesPerSecond: _Optional[float] = ..., totalMemoryKB: _Optional[int] = ...) -> None: ...

class OpenFileHandle(_message.Message):
    __slots__ = ("fileHandle", "processId", "processPath", "filePath", "isDirectory", "openTime", "specialCommand")
    FILEHANDLE_FIELD_NUMBER: _ClassVar[int]
    PROCESSID_FIELD_NUMBER: _ClassVar[int]
    PROCESSPATH_FIELD_NUMBER: _ClassVar[int]
    FILEPATH_FIELD_NUMBER: _ClassVar[int]
    ISDIRECTORY_FIELD_NUMBER: _ClassVar[int]
    OPENTIME_FIELD_NUMBER: _ClassVar[int]
    SPECIALCOMMAND_FIELD_NUMBER: _ClassVar[int]
    fileHandle: int
    processId: int
    processPath: str
    filePath: str
    isDirectory: bool
    openTime: _timestamp_pb2.Timestamp
    specialCommand: str
    def __init__(self, fileHandle: _Optional[int] = ..., processId: _Optional[int] = ..., processPath: _Optional[str] = ..., filePath: _Optional[str] = ..., isDirectory: bool = ..., openTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., specialCommand: _Optional[str] = ...) -> None: ...

class OpenFileHandleList(_message.Message):
    __slots__ = ("openFileHandles",)
    OPENFILEHANDLES_FIELD_NUMBER: _ClassVar[int]
    openFileHandles: _containers.RepeatedCompositeFieldContainer[OpenFileHandle]
    def __init__(self, openFileHandles: _Optional[_Iterable[_Union[OpenFileHandle, _Mapping]]] = ...) -> None: ...

class MountOption(_message.Message):
    __slots__ = ("mountPoint", "sourceDir", "localMount", "readOnly", "autoMount", "uid", "gid", "permissions", "name")
    MOUNTPOINT_FIELD_NUMBER: _ClassVar[int]
    SOURCEDIR_FIELD_NUMBER: _ClassVar[int]
    LOCALMOUNT_FIELD_NUMBER: _ClassVar[int]
    READONLY_FIELD_NUMBER: _ClassVar[int]
    AUTOMOUNT_FIELD_NUMBER: _ClassVar[int]
    UID_FIELD_NUMBER: _ClassVar[int]
    GID_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    mountPoint: str
    sourceDir: str
    localMount: bool
    readOnly: bool
    autoMount: bool
    uid: int
    gid: int
    permissions: str
    name: str
    def __init__(self, mountPoint: _Optional[str] = ..., sourceDir: _Optional[str] = ..., localMount: bool = ..., readOnly: bool = ..., autoMount: bool = ..., uid: _Optional[int] = ..., gid: _Optional[int] = ..., permissions: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class MountPoint(_message.Message):
    __slots__ = ("mountPoint", "sourceDir", "localMount", "readOnly", "autoMount", "uid", "gid", "permissions", "isMounted", "failReason")
    MOUNTPOINT_FIELD_NUMBER: _ClassVar[int]
    SOURCEDIR_FIELD_NUMBER: _ClassVar[int]
    LOCALMOUNT_FIELD_NUMBER: _ClassVar[int]
    READONLY_FIELD_NUMBER: _ClassVar[int]
    AUTOMOUNT_FIELD_NUMBER: _ClassVar[int]
    UID_FIELD_NUMBER: _ClassVar[int]
    GID_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    ISMOUNTED_FIELD_NUMBER: _ClassVar[int]
    FAILREASON_FIELD_NUMBER: _ClassVar[int]
    mountPoint: str
    sourceDir: str
    localMount: bool
    readOnly: bool
    autoMount: bool
    uid: int
    gid: int
    permissions: str
    isMounted: bool
    failReason: str
    def __init__(self, mountPoint: _Optional[str] = ..., sourceDir: _Optional[str] = ..., localMount: bool = ..., readOnly: bool = ..., autoMount: bool = ..., uid: _Optional[int] = ..., gid: _Optional[int] = ..., permissions: _Optional[str] = ..., isMounted: bool = ..., failReason: _Optional[str] = ...) -> None: ...

class MountPointRequest(_message.Message):
    __slots__ = ("MountPoint",)
    MOUNTPOINT_FIELD_NUMBER: _ClassVar[int]
    MountPoint: str
    def __init__(self, MountPoint: _Optional[str] = ...) -> None: ...

class GetMountPointsResult(_message.Message):
    __slots__ = ("mountPoints",)
    MOUNTPOINTS_FIELD_NUMBER: _ClassVar[int]
    mountPoints: _containers.RepeatedCompositeFieldContainer[MountPoint]
    def __init__(self, mountPoints: _Optional[_Iterable[_Union[MountPoint, _Mapping]]] = ...) -> None: ...

class MountPointResult(_message.Message):
    __slots__ = ("success", "failReason")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    FAILREASON_FIELD_NUMBER: _ClassVar[int]
    success: bool
    failReason: str
    def __init__(self, success: bool = ..., failReason: _Optional[str] = ...) -> None: ...

class UpdateMountPointRequest(_message.Message):
    __slots__ = ("mountPoint", "newMountOption")
    MOUNTPOINT_FIELD_NUMBER: _ClassVar[int]
    NEWMOUNTOPTION_FIELD_NUMBER: _ClassVar[int]
    mountPoint: str
    newMountOption: MountOption
    def __init__(self, mountPoint: _Optional[str] = ..., newMountOption: _Optional[_Union[MountOption, _Mapping]] = ...) -> None: ...

class GetAvailableDriveLettersRequest(_message.Message):
    __slots__ = ("includeCloudDrive",)
    INCLUDECLOUDDRIVE_FIELD_NUMBER: _ClassVar[int]
    includeCloudDrive: bool
    def __init__(self, includeCloudDrive: bool = ...) -> None: ...

class GetAvailableDriveLettersResult(_message.Message):
    __slots__ = ("driveLetters",)
    DRIVELETTERS_FIELD_NUMBER: _ClassVar[int]
    driveLetters: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, driveLetters: _Optional[_Iterable[str]] = ...) -> None: ...

class HasDriveLettersResult(_message.Message):
    __slots__ = ("hasDriveLetters",)
    HASDRIVELETTERS_FIELD_NUMBER: _ClassVar[int]
    hasDriveLetters: bool
    def __init__(self, hasDriveLetters: bool = ...) -> None: ...

class LocalGetSubFilesRequest(_message.Message):
    __slots__ = ("parentFolder", "folderOnly", "includeCloudDrive", "includeAvailableDrive")
    PARENTFOLDER_FIELD_NUMBER: _ClassVar[int]
    FOLDERONLY_FIELD_NUMBER: _ClassVar[int]
    INCLUDECLOUDDRIVE_FIELD_NUMBER: _ClassVar[int]
    INCLUDEAVAILABLEDRIVE_FIELD_NUMBER: _ClassVar[int]
    parentFolder: str
    folderOnly: bool
    includeCloudDrive: bool
    includeAvailableDrive: bool
    def __init__(self, parentFolder: _Optional[str] = ..., folderOnly: bool = ..., includeCloudDrive: bool = ..., includeAvailableDrive: bool = ...) -> None: ...

class LocalGetSubFilesResult(_message.Message):
    __slots__ = ("subFiles",)
    SUBFILES_FIELD_NUMBER: _ClassVar[int]
    subFiles: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, subFiles: _Optional[_Iterable[str]] = ...) -> None: ...

class PushMessage(_message.Message):
    __slots__ = ("clouddriveVersion",)
    CLOUDDRIVEVERSION_FIELD_NUMBER: _ClassVar[int]
    clouddriveVersion: str
    def __init__(self, clouddriveVersion: _Optional[str] = ...) -> None: ...

class GetAllTasksCountResult(_message.Message):
    __slots__ = ("downloadCount", "uploadCount", "copyTaskCount", "pushMessage", "hasUpdate", "uploadFileStatusChanges")
    DOWNLOADCOUNT_FIELD_NUMBER: _ClassVar[int]
    UPLOADCOUNT_FIELD_NUMBER: _ClassVar[int]
    COPYTASKCOUNT_FIELD_NUMBER: _ClassVar[int]
    PUSHMESSAGE_FIELD_NUMBER: _ClassVar[int]
    HASUPDATE_FIELD_NUMBER: _ClassVar[int]
    UPLOADFILESTATUSCHANGES_FIELD_NUMBER: _ClassVar[int]
    downloadCount: int
    uploadCount: int
    copyTaskCount: int
    pushMessage: PushMessage
    hasUpdate: bool
    uploadFileStatusChanges: _containers.RepeatedCompositeFieldContainer[UploadFileInfo]
    def __init__(self, downloadCount: _Optional[int] = ..., uploadCount: _Optional[int] = ..., copyTaskCount: _Optional[int] = ..., pushMessage: _Optional[_Union[PushMessage, _Mapping]] = ..., hasUpdate: bool = ..., uploadFileStatusChanges: _Optional[_Iterable[_Union[UploadFileInfo, _Mapping]]] = ...) -> None: ...

class FileSystemChange(_message.Message):
    __slots__ = ("changeType", "isDirectory", "path", "newPath", "theFile")
    class ChangeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CREATE: _ClassVar[FileSystemChange.ChangeType]
        DELETE: _ClassVar[FileSystemChange.ChangeType]
        RENAME: _ClassVar[FileSystemChange.ChangeType]
    CREATE: FileSystemChange.ChangeType
    DELETE: FileSystemChange.ChangeType
    RENAME: FileSystemChange.ChangeType
    CHANGETYPE_FIELD_NUMBER: _ClassVar[int]
    ISDIRECTORY_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    NEWPATH_FIELD_NUMBER: _ClassVar[int]
    THEFILE_FIELD_NUMBER: _ClassVar[int]
    changeType: FileSystemChange.ChangeType
    isDirectory: bool
    path: str
    newPath: str
    theFile: CloudDriveFile
    def __init__(self, changeType: _Optional[_Union[FileSystemChange.ChangeType, str]] = ..., isDirectory: bool = ..., path: _Optional[str] = ..., newPath: _Optional[str] = ..., theFile: _Optional[_Union[CloudDriveFile, _Mapping]] = ...) -> None: ...

class UpdateStatus(_message.Message):
    __slots__ = ("updatePhase", "newVersion", "message", "clouddriveVersion", "downloadedBytes", "totalBytes")
    class UpdatePhase(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        NO_UPDATE: _ClassVar[UpdateStatus.UpdatePhase]
        DOWNLOADING: _ClassVar[UpdateStatus.UpdatePhase]
        READY_TO_UPDATE: _ClassVar[UpdateStatus.UpdatePhase]
        UPDATING: _ClassVar[UpdateStatus.UpdatePhase]
        UPDATE_SUCCESS: _ClassVar[UpdateStatus.UpdatePhase]
        UPDATE_FAILED: _ClassVar[UpdateStatus.UpdatePhase]
    NO_UPDATE: UpdateStatus.UpdatePhase
    DOWNLOADING: UpdateStatus.UpdatePhase
    READY_TO_UPDATE: UpdateStatus.UpdatePhase
    UPDATING: UpdateStatus.UpdatePhase
    UPDATE_SUCCESS: UpdateStatus.UpdatePhase
    UPDATE_FAILED: UpdateStatus.UpdatePhase
    UPDATEPHASE_FIELD_NUMBER: _ClassVar[int]
    NEWVERSION_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CLOUDDRIVEVERSION_FIELD_NUMBER: _ClassVar[int]
    DOWNLOADEDBYTES_FIELD_NUMBER: _ClassVar[int]
    TOTALBYTES_FIELD_NUMBER: _ClassVar[int]
    updatePhase: UpdateStatus.UpdatePhase
    newVersion: str
    message: str
    clouddriveVersion: str
    downloadedBytes: int
    totalBytes: int
    def __init__(self, updatePhase: _Optional[_Union[UpdateStatus.UpdatePhase, str]] = ..., newVersion: _Optional[str] = ..., message: _Optional[str] = ..., clouddriveVersion: _Optional[str] = ..., downloadedBytes: _Optional[int] = ..., totalBytes: _Optional[int] = ...) -> None: ...

class TransferTaskStatus(_message.Message):
    __slots__ = ("downloadCount", "uploadCount", "clouddriveVersion", "uploadFileStatusChanges", "hasUpdate", "copyTaskCount")
    DOWNLOADCOUNT_FIELD_NUMBER: _ClassVar[int]
    UPLOADCOUNT_FIELD_NUMBER: _ClassVar[int]
    CLOUDDRIVEVERSION_FIELD_NUMBER: _ClassVar[int]
    UPLOADFILESTATUSCHANGES_FIELD_NUMBER: _ClassVar[int]
    HASUPDATE_FIELD_NUMBER: _ClassVar[int]
    COPYTASKCOUNT_FIELD_NUMBER: _ClassVar[int]
    downloadCount: int
    uploadCount: int
    clouddriveVersion: str
    uploadFileStatusChanges: _containers.RepeatedCompositeFieldContainer[UploadFileInfo]
    hasUpdate: bool
    copyTaskCount: int
    def __init__(self, downloadCount: _Optional[int] = ..., uploadCount: _Optional[int] = ..., clouddriveVersion: _Optional[str] = ..., uploadFileStatusChanges: _Optional[_Iterable[_Union[UploadFileInfo, _Mapping]]] = ..., hasUpdate: bool = ..., copyTaskCount: _Optional[int] = ...) -> None: ...

class ExitedMessage(_message.Message):
    __slots__ = ("exitReason", "message")
    class ExitReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[ExitedMessage.ExitReason]
        KICKEDOUT_BY_USER: _ClassVar[ExitedMessage.ExitReason]
        KICKEDOUT_BY_SERVER: _ClassVar[ExitedMessage.ExitReason]
        PASSWORD_CHANGED: _ClassVar[ExitedMessage.ExitReason]
        RESTART: _ClassVar[ExitedMessage.ExitReason]
        SHUTDOWN: _ClassVar[ExitedMessage.ExitReason]
    UNKNOWN: ExitedMessage.ExitReason
    KICKEDOUT_BY_USER: ExitedMessage.ExitReason
    KICKEDOUT_BY_SERVER: ExitedMessage.ExitReason
    PASSWORD_CHANGED: ExitedMessage.ExitReason
    RESTART: ExitedMessage.ExitReason
    SHUTDOWN: ExitedMessage.ExitReason
    EXITREASON_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    exitReason: ExitedMessage.ExitReason
    message: str
    def __init__(self, exitReason: _Optional[_Union[ExitedMessage.ExitReason, str]] = ..., message: _Optional[str] = ...) -> None: ...

class FileSystemChangeList(_message.Message):
    __slots__ = ("fileSystemChanges",)
    FILESYSTEMCHANGES_FIELD_NUMBER: _ClassVar[int]
    fileSystemChanges: _containers.RepeatedCompositeFieldContainer[FileSystemChange]
    def __init__(self, fileSystemChanges: _Optional[_Iterable[_Union[FileSystemChange, _Mapping]]] = ...) -> None: ...

class MountPointChange(_message.Message):
    __slots__ = ("actionType", "mountPoint", "success", "failReason")
    class ActionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        MOUNT: _ClassVar[MountPointChange.ActionType]
        UNMOUNT: _ClassVar[MountPointChange.ActionType]
    MOUNT: MountPointChange.ActionType
    UNMOUNT: MountPointChange.ActionType
    ACTIONTYPE_FIELD_NUMBER: _ClassVar[int]
    MOUNTPOINT_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    FAILREASON_FIELD_NUMBER: _ClassVar[int]
    actionType: MountPointChange.ActionType
    mountPoint: str
    success: bool
    failReason: str
    def __init__(self, actionType: _Optional[_Union[MountPointChange.ActionType, str]] = ..., mountPoint: _Optional[str] = ..., success: bool = ..., failReason: _Optional[str] = ...) -> None: ...

class LogMessage(_message.Message):
    __slots__ = ("level", "message", "target", "timestamp", "fields")
    class LogLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        TRACE: _ClassVar[LogMessage.LogLevel]
        DEBUG: _ClassVar[LogMessage.LogLevel]
        INFO: _ClassVar[LogMessage.LogLevel]
        WARN: _ClassVar[LogMessage.LogLevel]
        ERROR: _ClassVar[LogMessage.LogLevel]
    TRACE: LogMessage.LogLevel
    DEBUG: LogMessage.LogLevel
    INFO: LogMessage.LogLevel
    WARN: LogMessage.LogLevel
    ERROR: LogMessage.LogLevel
    class FieldsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    level: LogMessage.LogLevel
    message: str
    target: str
    timestamp: _timestamp_pb2.Timestamp
    fields: _containers.ScalarMap[str, str]
    def __init__(self, level: _Optional[_Union[LogMessage.LogLevel, str]] = ..., message: _Optional[str] = ..., target: _Optional[str] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., fields: _Optional[_Mapping[str, str]] = ...) -> None: ...

class CloudDrivePushMessage(_message.Message):
    __slots__ = ("messageType", "transferTaskStatus", "updateStatus", "exitedMessage", "fileSystemChange", "mountPointChange", "logMessage", "mergeTaskUpdate")
    class MessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        DOWNLOADER_COUNT: _ClassVar[CloudDrivePushMessage.MessageType]
        UPLOADER_COUNT: _ClassVar[CloudDrivePushMessage.MessageType]
        UPDATE_STATUS: _ClassVar[CloudDrivePushMessage.MessageType]
        FORCE_EXIT: _ClassVar[CloudDrivePushMessage.MessageType]
        FILE_SYSTEM_CHANGE: _ClassVar[CloudDrivePushMessage.MessageType]
        MOUNT_POINT_CHANGE: _ClassVar[CloudDrivePushMessage.MessageType]
        COPY_TASK_COUNT: _ClassVar[CloudDrivePushMessage.MessageType]
        LOG_MESSAGE: _ClassVar[CloudDrivePushMessage.MessageType]
        MERGE_TASKS: _ClassVar[CloudDrivePushMessage.MessageType]
    DOWNLOADER_COUNT: CloudDrivePushMessage.MessageType
    UPLOADER_COUNT: CloudDrivePushMessage.MessageType
    UPDATE_STATUS: CloudDrivePushMessage.MessageType
    FORCE_EXIT: CloudDrivePushMessage.MessageType
    FILE_SYSTEM_CHANGE: CloudDrivePushMessage.MessageType
    MOUNT_POINT_CHANGE: CloudDrivePushMessage.MessageType
    COPY_TASK_COUNT: CloudDrivePushMessage.MessageType
    LOG_MESSAGE: CloudDrivePushMessage.MessageType
    MERGE_TASKS: CloudDrivePushMessage.MessageType
    MESSAGETYPE_FIELD_NUMBER: _ClassVar[int]
    TRANSFERTASKSTATUS_FIELD_NUMBER: _ClassVar[int]
    UPDATESTATUS_FIELD_NUMBER: _ClassVar[int]
    EXITEDMESSAGE_FIELD_NUMBER: _ClassVar[int]
    FILESYSTEMCHANGE_FIELD_NUMBER: _ClassVar[int]
    MOUNTPOINTCHANGE_FIELD_NUMBER: _ClassVar[int]
    LOGMESSAGE_FIELD_NUMBER: _ClassVar[int]
    MERGETASKUPDATE_FIELD_NUMBER: _ClassVar[int]
    messageType: CloudDrivePushMessage.MessageType
    transferTaskStatus: TransferTaskStatus
    updateStatus: UpdateStatus
    exitedMessage: ExitedMessage
    fileSystemChange: FileSystemChange
    mountPointChange: MountPointChange
    logMessage: LogMessage
    mergeTaskUpdate: MergeTaskUpdate
    def __init__(self, messageType: _Optional[_Union[CloudDrivePushMessage.MessageType, str]] = ..., transferTaskStatus: _Optional[_Union[TransferTaskStatus, _Mapping]] = ..., updateStatus: _Optional[_Union[UpdateStatus, _Mapping]] = ..., exitedMessage: _Optional[_Union[ExitedMessage, _Mapping]] = ..., fileSystemChange: _Optional[_Union[FileSystemChange, _Mapping]] = ..., mountPointChange: _Optional[_Union[MountPointChange, _Mapping]] = ..., logMessage: _Optional[_Union[LogMessage, _Mapping]] = ..., mergeTaskUpdate: _Optional[_Union[MergeTaskUpdate, _Mapping]] = ...) -> None: ...

class MergeTaskUpdate(_message.Message):
    __slots__ = ("mergeTasks", "lastMergedPath", "lastMergedNewPath")
    MERGETASKS_FIELD_NUMBER: _ClassVar[int]
    LASTMERGEDPATH_FIELD_NUMBER: _ClassVar[int]
    LASTMERGEDNEWPATH_FIELD_NUMBER: _ClassVar[int]
    mergeTasks: _containers.RepeatedCompositeFieldContainer[MergeTask]
    lastMergedPath: str
    lastMergedNewPath: str
    def __init__(self, mergeTasks: _Optional[_Iterable[_Union[MergeTask, _Mapping]]] = ..., lastMergedPath: _Optional[str] = ..., lastMergedNewPath: _Optional[str] = ...) -> None: ...

class GetDownloadFileCountResult(_message.Message):
    __slots__ = ("fileCount",)
    FILECOUNT_FIELD_NUMBER: _ClassVar[int]
    fileCount: int
    def __init__(self, fileCount: _Optional[int] = ...) -> None: ...

class DownloadFileInfo(_message.Message):
    __slots__ = ("filePath", "fileLength", "totalBufferUsed", "downloadThreadCount", "process", "detailDownloadInfo", "lastDownloadError", "bytesPerSecond")
    FILEPATH_FIELD_NUMBER: _ClassVar[int]
    FILELENGTH_FIELD_NUMBER: _ClassVar[int]
    TOTALBUFFERUSED_FIELD_NUMBER: _ClassVar[int]
    DOWNLOADTHREADCOUNT_FIELD_NUMBER: _ClassVar[int]
    PROCESS_FIELD_NUMBER: _ClassVar[int]
    DETAILDOWNLOADINFO_FIELD_NUMBER: _ClassVar[int]
    LASTDOWNLOADERROR_FIELD_NUMBER: _ClassVar[int]
    BYTESPERSECOND_FIELD_NUMBER: _ClassVar[int]
    filePath: str
    fileLength: int
    totalBufferUsed: int
    downloadThreadCount: int
    process: _containers.RepeatedScalarFieldContainer[str]
    detailDownloadInfo: str
    lastDownloadError: str
    bytesPerSecond: float
    def __init__(self, filePath: _Optional[str] = ..., fileLength: _Optional[int] = ..., totalBufferUsed: _Optional[int] = ..., downloadThreadCount: _Optional[int] = ..., process: _Optional[_Iterable[str]] = ..., detailDownloadInfo: _Optional[str] = ..., lastDownloadError: _Optional[str] = ..., bytesPerSecond: _Optional[float] = ...) -> None: ...

class GetDownloadFileListResult(_message.Message):
    __slots__ = ("globalBytesPerSecond", "downloadFiles")
    GLOBALBYTESPERSECOND_FIELD_NUMBER: _ClassVar[int]
    DOWNLOADFILES_FIELD_NUMBER: _ClassVar[int]
    globalBytesPerSecond: float
    downloadFiles: _containers.RepeatedCompositeFieldContainer[DownloadFileInfo]
    def __init__(self, globalBytesPerSecond: _Optional[float] = ..., downloadFiles: _Optional[_Iterable[_Union[DownloadFileInfo, _Mapping]]] = ...) -> None: ...

class GetUploadFileCountResult(_message.Message):
    __slots__ = ("fileCount",)
    FILECOUNT_FIELD_NUMBER: _ClassVar[int]
    fileCount: int
    def __init__(self, fileCount: _Optional[int] = ...) -> None: ...

class UploadFileInfo(_message.Message):
    __slots__ = ("key", "destPath", "size", "transferedBytes", "status", "errorMessage", "operatorType", "statusEnum")
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        WaitforPreprocessing: _ClassVar[UploadFileInfo.Status]
        Preprocessing: _ClassVar[UploadFileInfo.Status]
        Cancelled: _ClassVar[UploadFileInfo.Status]
        Transfer: _ClassVar[UploadFileInfo.Status]
        Pause: _ClassVar[UploadFileInfo.Status]
        Finish: _ClassVar[UploadFileInfo.Status]
        Skipped: _ClassVar[UploadFileInfo.Status]
        Inqueue: _ClassVar[UploadFileInfo.Status]
        Ignored: _ClassVar[UploadFileInfo.Status]
        Error: _ClassVar[UploadFileInfo.Status]
        FatalError: _ClassVar[UploadFileInfo.Status]
    WaitforPreprocessing: UploadFileInfo.Status
    Preprocessing: UploadFileInfo.Status
    Cancelled: UploadFileInfo.Status
    Transfer: UploadFileInfo.Status
    Pause: UploadFileInfo.Status
    Finish: UploadFileInfo.Status
    Skipped: UploadFileInfo.Status
    Inqueue: UploadFileInfo.Status
    Ignored: UploadFileInfo.Status
    Error: UploadFileInfo.Status
    FatalError: UploadFileInfo.Status
    class OperatorType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Mount: _ClassVar[UploadFileInfo.OperatorType]
        Copy: _ClassVar[UploadFileInfo.OperatorType]
        BackupFile: _ClassVar[UploadFileInfo.OperatorType]
        RemoteUpload: _ClassVar[UploadFileInfo.OperatorType]
    Mount: UploadFileInfo.OperatorType
    Copy: UploadFileInfo.OperatorType
    BackupFile: UploadFileInfo.OperatorType
    RemoteUpload: UploadFileInfo.OperatorType
    KEY_FIELD_NUMBER: _ClassVar[int]
    DESTPATH_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    TRANSFEREDBYTES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    OPERATORTYPE_FIELD_NUMBER: _ClassVar[int]
    STATUSENUM_FIELD_NUMBER: _ClassVar[int]
    key: str
    destPath: str
    size: int
    transferedBytes: int
    status: str
    errorMessage: str
    operatorType: UploadFileInfo.OperatorType
    statusEnum: UploadFileInfo.Status
    def __init__(self, key: _Optional[str] = ..., destPath: _Optional[str] = ..., size: _Optional[int] = ..., transferedBytes: _Optional[int] = ..., status: _Optional[str] = ..., errorMessage: _Optional[str] = ..., operatorType: _Optional[_Union[UploadFileInfo.OperatorType, str]] = ..., statusEnum: _Optional[_Union[UploadFileInfo.Status, str]] = ...) -> None: ...

class GetUploadFileListRequest(_message.Message):
    __slots__ = ("getAll", "itemsPerPage", "pageNumber", "filter", "statusFilter", "operatorTypeFilter")
    GETALL_FIELD_NUMBER: _ClassVar[int]
    ITEMSPERPAGE_FIELD_NUMBER: _ClassVar[int]
    PAGENUMBER_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    STATUSFILTER_FIELD_NUMBER: _ClassVar[int]
    OPERATORTYPEFILTER_FIELD_NUMBER: _ClassVar[int]
    getAll: bool
    itemsPerPage: int
    pageNumber: int
    filter: str
    statusFilter: UploadFileInfo.Status
    operatorTypeFilter: UploadFileInfo.OperatorType
    def __init__(self, getAll: bool = ..., itemsPerPage: _Optional[int] = ..., pageNumber: _Optional[int] = ..., filter: _Optional[str] = ..., statusFilter: _Optional[_Union[UploadFileInfo.Status, str]] = ..., operatorTypeFilter: _Optional[_Union[UploadFileInfo.OperatorType, str]] = ...) -> None: ...

class GetUploadFileListResult(_message.Message):
    __slots__ = ("totalCount", "uploadFiles", "globalBytesPerSecond", "totalBytes", "finishedBytes")
    TOTALCOUNT_FIELD_NUMBER: _ClassVar[int]
    UPLOADFILES_FIELD_NUMBER: _ClassVar[int]
    GLOBALBYTESPERSECOND_FIELD_NUMBER: _ClassVar[int]
    TOTALBYTES_FIELD_NUMBER: _ClassVar[int]
    FINISHEDBYTES_FIELD_NUMBER: _ClassVar[int]
    totalCount: int
    uploadFiles: _containers.RepeatedCompositeFieldContainer[UploadFileInfo]
    globalBytesPerSecond: float
    totalBytes: int
    finishedBytes: int
    def __init__(self, totalCount: _Optional[int] = ..., uploadFiles: _Optional[_Iterable[_Union[UploadFileInfo, _Mapping]]] = ..., globalBytesPerSecond: _Optional[float] = ..., totalBytes: _Optional[int] = ..., finishedBytes: _Optional[int] = ...) -> None: ...

class TaskError(_message.Message):
    __slots__ = ("time", "message")
    TIME_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    time: _timestamp_pb2.Timestamp
    message: str
    def __init__(self, time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., message: _Optional[str] = ...) -> None: ...

class CopyTaskRequest(_message.Message):
    __slots__ = ("sourcePath", "destPath")
    SOURCEPATH_FIELD_NUMBER: _ClassVar[int]
    DESTPATH_FIELD_NUMBER: _ClassVar[int]
    sourcePath: str
    destPath: str
    def __init__(self, sourcePath: _Optional[str] = ..., destPath: _Optional[str] = ...) -> None: ...

class PauseCopyTaskRequest(_message.Message):
    __slots__ = ("sourcePath", "destPath", "pause")
    SOURCEPATH_FIELD_NUMBER: _ClassVar[int]
    DESTPATH_FIELD_NUMBER: _ClassVar[int]
    PAUSE_FIELD_NUMBER: _ClassVar[int]
    sourcePath: str
    destPath: str
    pause: bool
    def __init__(self, sourcePath: _Optional[str] = ..., destPath: _Optional[str] = ..., pause: bool = ...) -> None: ...

class CopyTaskBatchRequest(_message.Message):
    __slots__ = ("taskKeys",)
    TASKKEYS_FIELD_NUMBER: _ClassVar[int]
    taskKeys: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, taskKeys: _Optional[_Iterable[str]] = ...) -> None: ...

class PauseAllCopyTasksRequest(_message.Message):
    __slots__ = ("pause",)
    PAUSE_FIELD_NUMBER: _ClassVar[int]
    pause: bool
    def __init__(self, pause: bool = ...) -> None: ...

class PauseCopyTasksRequest(_message.Message):
    __slots__ = ("taskKeys", "pause")
    TASKKEYS_FIELD_NUMBER: _ClassVar[int]
    PAUSE_FIELD_NUMBER: _ClassVar[int]
    taskKeys: _containers.RepeatedScalarFieldContainer[str]
    pause: bool
    def __init__(self, taskKeys: _Optional[_Iterable[str]] = ..., pause: bool = ...) -> None: ...

class BatchOperationResult(_message.Message):
    __slots__ = ("success", "affectedCount", "errorMessage")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    AFFECTEDCOUNT_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    affectedCount: int
    errorMessage: str
    def __init__(self, success: bool = ..., affectedCount: _Optional[int] = ..., errorMessage: _Optional[str] = ...) -> None: ...

class MergeTask(_message.Message):
    __slots__ = ("sourcePath", "destPath", "status", "mergedFiles", "mergedFolders", "startTime", "endTime", "errorMessage", "conflictPolicy", "operationType")
    class TaskStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Pending: _ClassVar[MergeTask.TaskStatus]
        Running: _ClassVar[MergeTask.TaskStatus]
        Completed: _ClassVar[MergeTask.TaskStatus]
        Failed: _ClassVar[MergeTask.TaskStatus]
        Cancelled: _ClassVar[MergeTask.TaskStatus]
    Pending: MergeTask.TaskStatus
    Running: MergeTask.TaskStatus
    Completed: MergeTask.TaskStatus
    Failed: MergeTask.TaskStatus
    Cancelled: MergeTask.TaskStatus
    class OperationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Move: _ClassVar[MergeTask.OperationType]
        Copy: _ClassVar[MergeTask.OperationType]
    Move: MergeTask.OperationType
    Copy: MergeTask.OperationType
    SOURCEPATH_FIELD_NUMBER: _ClassVar[int]
    DESTPATH_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MERGEDFILES_FIELD_NUMBER: _ClassVar[int]
    MERGEDFOLDERS_FIELD_NUMBER: _ClassVar[int]
    STARTTIME_FIELD_NUMBER: _ClassVar[int]
    ENDTIME_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    CONFLICTPOLICY_FIELD_NUMBER: _ClassVar[int]
    OPERATIONTYPE_FIELD_NUMBER: _ClassVar[int]
    sourcePath: str
    destPath: str
    status: MergeTask.TaskStatus
    mergedFiles: int
    mergedFolders: int
    startTime: _timestamp_pb2.Timestamp
    endTime: _timestamp_pb2.Timestamp
    errorMessage: str
    conflictPolicy: MoveFileRequest.ConflictPolicy
    operationType: MergeTask.OperationType
    def __init__(self, sourcePath: _Optional[str] = ..., destPath: _Optional[str] = ..., status: _Optional[_Union[MergeTask.TaskStatus, str]] = ..., mergedFiles: _Optional[int] = ..., mergedFolders: _Optional[int] = ..., startTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., endTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., errorMessage: _Optional[str] = ..., conflictPolicy: _Optional[_Union[MoveFileRequest.ConflictPolicy, str]] = ..., operationType: _Optional[_Union[MergeTask.OperationType, str]] = ...) -> None: ...

class GetMergeTasksResult(_message.Message):
    __slots__ = ("mergeTasks",)
    MERGETASKS_FIELD_NUMBER: _ClassVar[int]
    mergeTasks: _containers.RepeatedCompositeFieldContainer[MergeTask]
    def __init__(self, mergeTasks: _Optional[_Iterable[_Union[MergeTask, _Mapping]]] = ...) -> None: ...

class CancelMergeTaskRequest(_message.Message):
    __slots__ = ("sourcePath", "destPath")
    SOURCEPATH_FIELD_NUMBER: _ClassVar[int]
    DESTPATH_FIELD_NUMBER: _ClassVar[int]
    sourcePath: str
    destPath: str
    def __init__(self, sourcePath: _Optional[str] = ..., destPath: _Optional[str] = ...) -> None: ...

class CopyTask(_message.Message):
    __slots__ = ("taskMode", "sourcePath", "destPath", "status", "totalFolders", "totalFiles", "failedFolders", "failedFiles", "uploadedFiles", "cancelledFiles", "skippedFiles", "totalBytes", "uploadedBytes", "paused", "errors", "startTime", "endTime")
    class TaskMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Copy: _ClassVar[CopyTask.TaskMode]
        Move: _ClassVar[CopyTask.TaskMode]
    Copy: CopyTask.TaskMode
    Move: CopyTask.TaskMode
    class TaskStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Pending: _ClassVar[CopyTask.TaskStatus]
        Scanning: _ClassVar[CopyTask.TaskStatus]
        Scanned: _ClassVar[CopyTask.TaskStatus]
        Completed: _ClassVar[CopyTask.TaskStatus]
        Failed: _ClassVar[CopyTask.TaskStatus]
    Pending: CopyTask.TaskStatus
    Scanning: CopyTask.TaskStatus
    Scanned: CopyTask.TaskStatus
    Completed: CopyTask.TaskStatus
    Failed: CopyTask.TaskStatus
    TASKMODE_FIELD_NUMBER: _ClassVar[int]
    SOURCEPATH_FIELD_NUMBER: _ClassVar[int]
    DESTPATH_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TOTALFOLDERS_FIELD_NUMBER: _ClassVar[int]
    TOTALFILES_FIELD_NUMBER: _ClassVar[int]
    FAILEDFOLDERS_FIELD_NUMBER: _ClassVar[int]
    FAILEDFILES_FIELD_NUMBER: _ClassVar[int]
    UPLOADEDFILES_FIELD_NUMBER: _ClassVar[int]
    CANCELLEDFILES_FIELD_NUMBER: _ClassVar[int]
    SKIPPEDFILES_FIELD_NUMBER: _ClassVar[int]
    TOTALBYTES_FIELD_NUMBER: _ClassVar[int]
    UPLOADEDBYTES_FIELD_NUMBER: _ClassVar[int]
    PAUSED_FIELD_NUMBER: _ClassVar[int]
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    STARTTIME_FIELD_NUMBER: _ClassVar[int]
    ENDTIME_FIELD_NUMBER: _ClassVar[int]
    taskMode: CopyTask.TaskMode
    sourcePath: str
    destPath: str
    status: CopyTask.TaskStatus
    totalFolders: int
    totalFiles: int
    failedFolders: int
    failedFiles: int
    uploadedFiles: int
    cancelledFiles: int
    skippedFiles: int
    totalBytes: int
    uploadedBytes: int
    paused: bool
    errors: _containers.RepeatedCompositeFieldContainer[TaskError]
    startTime: _timestamp_pb2.Timestamp
    endTime: _timestamp_pb2.Timestamp
    def __init__(self, taskMode: _Optional[_Union[CopyTask.TaskMode, str]] = ..., sourcePath: _Optional[str] = ..., destPath: _Optional[str] = ..., status: _Optional[_Union[CopyTask.TaskStatus, str]] = ..., totalFolders: _Optional[int] = ..., totalFiles: _Optional[int] = ..., failedFolders: _Optional[int] = ..., failedFiles: _Optional[int] = ..., uploadedFiles: _Optional[int] = ..., cancelledFiles: _Optional[int] = ..., skippedFiles: _Optional[int] = ..., totalBytes: _Optional[int] = ..., uploadedBytes: _Optional[int] = ..., paused: bool = ..., errors: _Optional[_Iterable[_Union[TaskError, _Mapping]]] = ..., startTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., endTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetCopyTaskResult(_message.Message):
    __slots__ = ("copyTasks",)
    COPYTASKS_FIELD_NUMBER: _ClassVar[int]
    copyTasks: _containers.RepeatedCompositeFieldContainer[CopyTask]
    def __init__(self, copyTasks: _Optional[_Iterable[_Union[CopyTask, _Mapping]]] = ...) -> None: ...

class MultpleUploadFileKeyRequest(_message.Message):
    __slots__ = ("keys",)
    KEYS_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, keys: _Optional[_Iterable[str]] = ...) -> None: ...

class Login115EditthiscookieRequest(_message.Message):
    __slots__ = ("editThiscookieString",)
    EDITTHISCOOKIESTRING_FIELD_NUMBER: _ClassVar[int]
    editThiscookieString: str
    def __init__(self, editThiscookieString: _Optional[str] = ...) -> None: ...

class Login115QrCodeRequest(_message.Message):
    __slots__ = ("platformString",)
    PLATFORMSTRING_FIELD_NUMBER: _ClassVar[int]
    platformString: str
    def __init__(self, platformString: _Optional[str] = ...) -> None: ...

class LoginAliyundriveOAuthRequest(_message.Message):
    __slots__ = ("refresh_token", "access_token", "expires_in")
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    refresh_token: str
    access_token: str
    expires_in: int
    def __init__(self, refresh_token: _Optional[str] = ..., access_token: _Optional[str] = ..., expires_in: _Optional[int] = ...) -> None: ...

class LoginAliyundriveRefreshtokenRequest(_message.Message):
    __slots__ = ("refreshToken", "useOpenAPI")
    REFRESHTOKEN_FIELD_NUMBER: _ClassVar[int]
    USEOPENAPI_FIELD_NUMBER: _ClassVar[int]
    refreshToken: str
    useOpenAPI: bool
    def __init__(self, refreshToken: _Optional[str] = ..., useOpenAPI: bool = ...) -> None: ...

class LoginAliyundriveQRCodeRequest(_message.Message):
    __slots__ = ("useOpenAPI",)
    USEOPENAPI_FIELD_NUMBER: _ClassVar[int]
    useOpenAPI: bool
    def __init__(self, useOpenAPI: bool = ...) -> None: ...

class LoginBaiduPanOAuthRequest(_message.Message):
    __slots__ = ("refresh_token", "access_token", "expires_in")
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    refresh_token: str
    access_token: str
    expires_in: int
    def __init__(self, refresh_token: _Optional[str] = ..., access_token: _Optional[str] = ..., expires_in: _Optional[int] = ...) -> None: ...

class LoginOneDriveOAuthRequest(_message.Message):
    __slots__ = ("refresh_token", "access_token", "expires_in")
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    refresh_token: str
    access_token: str
    expires_in: int
    def __init__(self, refresh_token: _Optional[str] = ..., access_token: _Optional[str] = ..., expires_in: _Optional[int] = ...) -> None: ...

class LoginGoogleDriveOAuthRequest(_message.Message):
    __slots__ = ("refresh_token", "access_token", "expires_in")
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    refresh_token: str
    access_token: str
    expires_in: int
    def __init__(self, refresh_token: _Optional[str] = ..., access_token: _Optional[str] = ..., expires_in: _Optional[int] = ...) -> None: ...

class LoginGoogleDriveRefreshTokenRequest(_message.Message):
    __slots__ = ("client_id", "client_secret", "refresh_token")
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_SECRET_FIELD_NUMBER: _ClassVar[int]
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    client_id: str
    client_secret: str
    refresh_token: str
    def __init__(self, client_id: _Optional[str] = ..., client_secret: _Optional[str] = ..., refresh_token: _Optional[str] = ...) -> None: ...

class LoginXunleiOAuthRequest(_message.Message):
    __slots__ = ("refresh_token", "access_token", "expires_in")
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    refresh_token: str
    access_token: str
    expires_in: int
    def __init__(self, refresh_token: _Optional[str] = ..., access_token: _Optional[str] = ..., expires_in: _Optional[int] = ...) -> None: ...

class LoginXunleiOpenOAuthRequest(_message.Message):
    __slots__ = ("refresh_token", "access_token", "expires_in")
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    refresh_token: str
    access_token: str
    expires_in: int
    def __init__(self, refresh_token: _Optional[str] = ..., access_token: _Optional[str] = ..., expires_in: _Optional[int] = ...) -> None: ...

class Login123panOAuthRequest(_message.Message):
    __slots__ = ("refresh_token", "access_token", "expires_in")
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    refresh_token: str
    access_token: str
    expires_in: int
    def __init__(self, refresh_token: _Optional[str] = ..., access_token: _Optional[str] = ..., expires_in: _Optional[int] = ...) -> None: ...

class Login115OpenOAuthRequest(_message.Message):
    __slots__ = ("refresh_token", "access_token", "expires_in")
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    refresh_token: str
    access_token: str
    expires_in: int
    def __init__(self, refresh_token: _Optional[str] = ..., access_token: _Optional[str] = ..., expires_in: _Optional[int] = ...) -> None: ...

class LoginWebDavRequest(_message.Message):
    __slots__ = ("serverUrl", "userName", "password", "doNotSyncToCloud")
    SERVERURL_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    DONOTSYNCTOCLOUD_FIELD_NUMBER: _ClassVar[int]
    serverUrl: str
    userName: str
    password: str
    doNotSyncToCloud: bool
    def __init__(self, serverUrl: _Optional[str] = ..., userName: _Optional[str] = ..., password: _Optional[str] = ..., doNotSyncToCloud: bool = ...) -> None: ...

class APILoginResult(_message.Message):
    __slots__ = ("success", "errorMessage")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    errorMessage: str
    def __init__(self, success: bool = ..., errorMessage: _Optional[str] = ...) -> None: ...

class AddLocalFolderRequest(_message.Message):
    __slots__ = ("localFolderPath",)
    LOCALFOLDERPATH_FIELD_NUMBER: _ClassVar[int]
    localFolderPath: str
    def __init__(self, localFolderPath: _Optional[str] = ...) -> None: ...

class LoginCloudDriveRequest(_message.Message):
    __slots__ = ("grpcUrl", "token", "insecureTls", "doNotSyncToCloud")
    GRPCURL_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    INSECURETLS_FIELD_NUMBER: _ClassVar[int]
    DONOTSYNCTOCLOUD_FIELD_NUMBER: _ClassVar[int]
    grpcUrl: str
    token: str
    insecureTls: bool
    doNotSyncToCloud: bool
    def __init__(self, grpcUrl: _Optional[str] = ..., token: _Optional[str] = ..., insecureTls: bool = ..., doNotSyncToCloud: bool = ...) -> None: ...

class RemoveCloudAPIRequest(_message.Message):
    __slots__ = ("cloudName", "userName", "permanentRemove")
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PERMANENTREMOVE_FIELD_NUMBER: _ClassVar[int]
    cloudName: str
    userName: str
    permanentRemove: bool
    def __init__(self, cloudName: _Optional[str] = ..., userName: _Optional[str] = ..., permanentRemove: bool = ...) -> None: ...

class CloudAPIRequest(_message.Message):
    __slots__ = ("cloudName", "userName")
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    cloudName: str
    userName: str
    def __init__(self, cloudName: _Optional[str] = ..., userName: _Optional[str] = ...) -> None: ...

class ProxyInfo(_message.Message):
    __slots__ = ("proxyType", "host", "port", "username", "password")
    PROXYTYPE_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    proxyType: ProxyType
    host: str
    port: int
    username: str
    password: str
    def __init__(self, proxyType: _Optional[_Union[ProxyType, str]] = ..., host: _Optional[str] = ..., port: _Optional[int] = ..., username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class GetCloudAPIConfigRequest(_message.Message):
    __slots__ = ("cloudName", "userName")
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    cloudName: str
    userName: str
    def __init__(self, cloudName: _Optional[str] = ..., userName: _Optional[str] = ...) -> None: ...

class CloudAPIList(_message.Message):
    __slots__ = ("apis",)
    APIS_FIELD_NUMBER: _ClassVar[int]
    apis: _containers.RepeatedCompositeFieldContainer[CloudAPI]
    def __init__(self, apis: _Optional[_Iterable[_Union[CloudAPI, _Mapping]]] = ...) -> None: ...

class CloudAPIConfig(_message.Message):
    __slots__ = ("maxDownloadThreads", "minReadLengthKB", "maxReadLengthKB", "defaultReadLengthKB", "maxBufferPoolSizeMB", "maxQueriesPerSecond", "forceIpv4", "apiProxy", "dataProxy", "customUserAgent", "maxUploadThreads", "insecureTls")
    MAXDOWNLOADTHREADS_FIELD_NUMBER: _ClassVar[int]
    MINREADLENGTHKB_FIELD_NUMBER: _ClassVar[int]
    MAXREADLENGTHKB_FIELD_NUMBER: _ClassVar[int]
    DEFAULTREADLENGTHKB_FIELD_NUMBER: _ClassVar[int]
    MAXBUFFERPOOLSIZEMB_FIELD_NUMBER: _ClassVar[int]
    MAXQUERIESPERSECOND_FIELD_NUMBER: _ClassVar[int]
    FORCEIPV4_FIELD_NUMBER: _ClassVar[int]
    APIPROXY_FIELD_NUMBER: _ClassVar[int]
    DATAPROXY_FIELD_NUMBER: _ClassVar[int]
    CUSTOMUSERAGENT_FIELD_NUMBER: _ClassVar[int]
    MAXUPLOADTHREADS_FIELD_NUMBER: _ClassVar[int]
    INSECURETLS_FIELD_NUMBER: _ClassVar[int]
    maxDownloadThreads: int
    minReadLengthKB: int
    maxReadLengthKB: int
    defaultReadLengthKB: int
    maxBufferPoolSizeMB: int
    maxQueriesPerSecond: float
    forceIpv4: bool
    apiProxy: ProxyInfo
    dataProxy: ProxyInfo
    customUserAgent: str
    maxUploadThreads: int
    insecureTls: bool
    def __init__(self, maxDownloadThreads: _Optional[int] = ..., minReadLengthKB: _Optional[int] = ..., maxReadLengthKB: _Optional[int] = ..., defaultReadLengthKB: _Optional[int] = ..., maxBufferPoolSizeMB: _Optional[int] = ..., maxQueriesPerSecond: _Optional[float] = ..., forceIpv4: bool = ..., apiProxy: _Optional[_Union[ProxyInfo, _Mapping]] = ..., dataProxy: _Optional[_Union[ProxyInfo, _Mapping]] = ..., customUserAgent: _Optional[str] = ..., maxUploadThreads: _Optional[int] = ..., insecureTls: bool = ...) -> None: ...

class SetCloudAPIConfigRequest(_message.Message):
    __slots__ = ("cloudName", "userName", "config")
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    cloudName: str
    userName: str
    config: CloudAPIConfig
    def __init__(self, cloudName: _Optional[str] = ..., userName: _Optional[str] = ..., config: _Optional[_Union[CloudAPIConfig, _Mapping]] = ...) -> None: ...

class CommandRequest(_message.Message):
    __slots__ = ("command",)
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    command: str
    def __init__(self, command: _Optional[str] = ...) -> None: ...

class CommandResult(_message.Message):
    __slots__ = ("result",)
    RESULT_FIELD_NUMBER: _ClassVar[int]
    result: str
    def __init__(self, result: _Optional[str] = ...) -> None: ...

class StringValue(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: str
    def __init__(self, value: _Optional[str] = ...) -> None: ...

class QRCodeScanMessage(_message.Message):
    __slots__ = ("messageType", "message")
    MESSAGETYPE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    messageType: QRCodeScanMessageType
    message: str
    def __init__(self, messageType: _Optional[_Union[QRCodeScanMessageType, str]] = ..., message: _Optional[str] = ...) -> None: ...

class StringList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, values: _Optional[_Iterable[str]] = ...) -> None: ...

class SystemSettings(_message.Message):
    __slots__ = ("dirCacheTimeToLiveSecs", "maxPreProcessTasks", "maxProcessTasks", "tempFileLocation", "syncWithCloud", "readDownloaderTimeoutSecs", "uploadDelaySecs", "processBlackList", "uploadIgnoredExtensions", "updateChannel", "maxDownloadSpeedKBytesPerSecond", "maxUploadSpeedKBytesPerSecond", "deviceName", "dirCachePersistence", "dirCacheDbLocation", "fileLogLevel", "terminalLogLevel", "backupLogLevel", "EnableAutoRegisterDevice", "realtimeLogLevel", "operatorPriorityOrder", "updateProxy")
    DIRCACHETIMETOLIVESECS_FIELD_NUMBER: _ClassVar[int]
    MAXPREPROCESSTASKS_FIELD_NUMBER: _ClassVar[int]
    MAXPROCESSTASKS_FIELD_NUMBER: _ClassVar[int]
    TEMPFILELOCATION_FIELD_NUMBER: _ClassVar[int]
    SYNCWITHCLOUD_FIELD_NUMBER: _ClassVar[int]
    READDOWNLOADERTIMEOUTSECS_FIELD_NUMBER: _ClassVar[int]
    UPLOADDELAYSECS_FIELD_NUMBER: _ClassVar[int]
    PROCESSBLACKLIST_FIELD_NUMBER: _ClassVar[int]
    UPLOADIGNOREDEXTENSIONS_FIELD_NUMBER: _ClassVar[int]
    UPDATECHANNEL_FIELD_NUMBER: _ClassVar[int]
    MAXDOWNLOADSPEEDKBYTESPERSECOND_FIELD_NUMBER: _ClassVar[int]
    MAXUPLOADSPEEDKBYTESPERSECOND_FIELD_NUMBER: _ClassVar[int]
    DEVICENAME_FIELD_NUMBER: _ClassVar[int]
    DIRCACHEPERSISTENCE_FIELD_NUMBER: _ClassVar[int]
    DIRCACHEDBLOCATION_FIELD_NUMBER: _ClassVar[int]
    FILELOGLEVEL_FIELD_NUMBER: _ClassVar[int]
    TERMINALLOGLEVEL_FIELD_NUMBER: _ClassVar[int]
    BACKUPLOGLEVEL_FIELD_NUMBER: _ClassVar[int]
    ENABLEAUTOREGISTERDEVICE_FIELD_NUMBER: _ClassVar[int]
    REALTIMELOGLEVEL_FIELD_NUMBER: _ClassVar[int]
    OPERATORPRIORITYORDER_FIELD_NUMBER: _ClassVar[int]
    UPDATEPROXY_FIELD_NUMBER: _ClassVar[int]
    dirCacheTimeToLiveSecs: int
    maxPreProcessTasks: int
    maxProcessTasks: int
    tempFileLocation: str
    syncWithCloud: bool
    readDownloaderTimeoutSecs: int
    uploadDelaySecs: int
    processBlackList: StringList
    uploadIgnoredExtensions: StringList
    updateChannel: UpdateChannel
    maxDownloadSpeedKBytesPerSecond: float
    maxUploadSpeedKBytesPerSecond: float
    deviceName: str
    dirCachePersistence: bool
    dirCacheDbLocation: str
    fileLogLevel: LogLevel
    terminalLogLevel: LogLevel
    backupLogLevel: LogLevel
    EnableAutoRegisterDevice: bool
    realtimeLogLevel: LogLevel
    operatorPriorityOrder: StringList
    updateProxy: ProxyInfo
    def __init__(self, dirCacheTimeToLiveSecs: _Optional[int] = ..., maxPreProcessTasks: _Optional[int] = ..., maxProcessTasks: _Optional[int] = ..., tempFileLocation: _Optional[str] = ..., syncWithCloud: bool = ..., readDownloaderTimeoutSecs: _Optional[int] = ..., uploadDelaySecs: _Optional[int] = ..., processBlackList: _Optional[_Union[StringList, _Mapping]] = ..., uploadIgnoredExtensions: _Optional[_Union[StringList, _Mapping]] = ..., updateChannel: _Optional[_Union[UpdateChannel, str]] = ..., maxDownloadSpeedKBytesPerSecond: _Optional[float] = ..., maxUploadSpeedKBytesPerSecond: _Optional[float] = ..., deviceName: _Optional[str] = ..., dirCachePersistence: bool = ..., dirCacheDbLocation: _Optional[str] = ..., fileLogLevel: _Optional[_Union[LogLevel, str]] = ..., terminalLogLevel: _Optional[_Union[LogLevel, str]] = ..., backupLogLevel: _Optional[_Union[LogLevel, str]] = ..., EnableAutoRegisterDevice: bool = ..., realtimeLogLevel: _Optional[_Union[LogLevel, str]] = ..., operatorPriorityOrder: _Optional[_Union[StringList, _Mapping]] = ..., updateProxy: _Optional[_Union[ProxyInfo, _Mapping]] = ...) -> None: ...

class SetDirCacheTimeRequest(_message.Message):
    __slots__ = ("path", "dirCachTimeToLiveSecs")
    PATH_FIELD_NUMBER: _ClassVar[int]
    DIRCACHTIMETOLIVESECS_FIELD_NUMBER: _ClassVar[int]
    path: str
    dirCachTimeToLiveSecs: int
    def __init__(self, path: _Optional[str] = ..., dirCachTimeToLiveSecs: _Optional[int] = ...) -> None: ...

class GetEffectiveDirCacheTimeRequest(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: str
    def __init__(self, path: _Optional[str] = ...) -> None: ...

class GetOpenFileTableRequest(_message.Message):
    __slots__ = ("includeDir",)
    INCLUDEDIR_FIELD_NUMBER: _ClassVar[int]
    includeDir: bool
    def __init__(self, includeDir: bool = ...) -> None: ...

class GetEffectiveDirCacheTimeResult(_message.Message):
    __slots__ = ("dirCacheTimeSecs",)
    DIRCACHETIMESECS_FIELD_NUMBER: _ClassVar[int]
    dirCacheTimeSecs: int
    def __init__(self, dirCacheTimeSecs: _Optional[int] = ...) -> None: ...

class UpdateResult(_message.Message):
    __slots__ = ("hasUpdate", "newVersion", "description")
    HASUPDATE_FIELD_NUMBER: _ClassVar[int]
    NEWVERSION_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    hasUpdate: bool
    newVersion: str
    description: str
    def __init__(self, hasUpdate: bool = ..., newVersion: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class OpenFileTable(_message.Message):
    __slots__ = ("openFileTable", "localOpenFileCount")
    class OpenFileTableEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: str
        def __init__(self, key: _Optional[int] = ..., value: _Optional[str] = ...) -> None: ...
    OPENFILETABLE_FIELD_NUMBER: _ClassVar[int]
    LOCALOPENFILECOUNT_FIELD_NUMBER: _ClassVar[int]
    openFileTable: _containers.ScalarMap[int, str]
    localOpenFileCount: int
    def __init__(self, openFileTable: _Optional[_Mapping[int, str]] = ..., localOpenFileCount: _Optional[int] = ...) -> None: ...

class DirCacheItem(_message.Message):
    __slots__ = ("insertTime", "timeToLiveSecs", "referencedSubfileLen")
    INSERTTIME_FIELD_NUMBER: _ClassVar[int]
    TIMETOLIVESECS_FIELD_NUMBER: _ClassVar[int]
    REFERENCEDSUBFILELEN_FIELD_NUMBER: _ClassVar[int]
    insertTime: _timestamp_pb2.Timestamp
    timeToLiveSecs: int
    referencedSubfileLen: int
    def __init__(self, insertTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., timeToLiveSecs: _Optional[int] = ..., referencedSubfileLen: _Optional[int] = ...) -> None: ...

class DirCacheTable(_message.Message):
    __slots__ = ("dirCacheTable",)
    class DirCacheTableEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: DirCacheItem
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[DirCacheItem, _Mapping]] = ...) -> None: ...
    DIRCACHETABLE_FIELD_NUMBER: _ClassVar[int]
    dirCacheTable: _containers.MessageMap[str, DirCacheItem]
    def __init__(self, dirCacheTable: _Optional[_Mapping[str, DirCacheItem]] = ...) -> None: ...

class TempFileTable(_message.Message):
    __slots__ = ("count", "tempFiles")
    COUNT_FIELD_NUMBER: _ClassVar[int]
    TEMPFILES_FIELD_NUMBER: _ClassVar[int]
    count: int
    tempFiles: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, count: _Optional[int] = ..., tempFiles: _Optional[_Iterable[str]] = ...) -> None: ...

class ConfirmEmailRequest(_message.Message):
    __slots__ = ("confirmCode",)
    CONFIRMCODE_FIELD_NUMBER: _ClassVar[int]
    confirmCode: str
    def __init__(self, confirmCode: _Optional[str] = ...) -> None: ...

class SendResetAccountEmailRequest(_message.Message):
    __slots__ = ("email",)
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    email: str
    def __init__(self, email: _Optional[str] = ...) -> None: ...

class ResetAccountRequest(_message.Message):
    __slots__ = ("resetCode", "newPassword")
    RESETCODE_FIELD_NUMBER: _ClassVar[int]
    NEWPASSWORD_FIELD_NUMBER: _ClassVar[int]
    resetCode: str
    newPassword: str
    def __init__(self, resetCode: _Optional[str] = ..., newPassword: _Optional[str] = ...) -> None: ...

class CloudDrivePlan(_message.Message):
    __slots__ = ("id", "name", "description", "price", "duration", "durationDescription", "isActive", "fontAwesomeIcon", "originalPrice", "planRoles")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    DURATIONDESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ISACTIVE_FIELD_NUMBER: _ClassVar[int]
    FONTAWESOMEICON_FIELD_NUMBER: _ClassVar[int]
    ORIGINALPRICE_FIELD_NUMBER: _ClassVar[int]
    PLANROLES_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    description: str
    price: float
    duration: int
    durationDescription: str
    isActive: bool
    fontAwesomeIcon: str
    originalPrice: float
    planRoles: _containers.RepeatedCompositeFieldContainer[AccountRole]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., price: _Optional[float] = ..., duration: _Optional[int] = ..., durationDescription: _Optional[str] = ..., isActive: bool = ..., fontAwesomeIcon: _Optional[str] = ..., originalPrice: _Optional[float] = ..., planRoles: _Optional[_Iterable[_Union[AccountRole, _Mapping]]] = ...) -> None: ...

class GetCloudDrivePlansResult(_message.Message):
    __slots__ = ("plans",)
    PLANS_FIELD_NUMBER: _ClassVar[int]
    plans: _containers.RepeatedCompositeFieldContainer[CloudDrivePlan]
    def __init__(self, plans: _Optional[_Iterable[_Union[CloudDrivePlan, _Mapping]]] = ...) -> None: ...

class JoinPlanRequest(_message.Message):
    __slots__ = ("planId", "couponCode")
    PLANID_FIELD_NUMBER: _ClassVar[int]
    COUPONCODE_FIELD_NUMBER: _ClassVar[int]
    planId: str
    couponCode: str
    def __init__(self, planId: _Optional[str] = ..., couponCode: _Optional[str] = ...) -> None: ...

class PaymentInfo(_message.Message):
    __slots__ = ("user_id", "plan_id", "paymentMethods", "coupon_code", "machine_id", "check_code")
    class PaymentMethodsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    PLAN_ID_FIELD_NUMBER: _ClassVar[int]
    PAYMENTMETHODS_FIELD_NUMBER: _ClassVar[int]
    COUPON_CODE_FIELD_NUMBER: _ClassVar[int]
    MACHINE_ID_FIELD_NUMBER: _ClassVar[int]
    CHECK_CODE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    plan_id: str
    paymentMethods: _containers.ScalarMap[str, str]
    coupon_code: str
    machine_id: str
    check_code: str
    def __init__(self, user_id: _Optional[str] = ..., plan_id: _Optional[str] = ..., paymentMethods: _Optional[_Mapping[str, str]] = ..., coupon_code: _Optional[str] = ..., machine_id: _Optional[str] = ..., check_code: _Optional[str] = ...) -> None: ...

class JoinPlanResult(_message.Message):
    __slots__ = ("success", "balance", "planName", "planDescription", "expireTime", "paymentInfo")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    BALANCE_FIELD_NUMBER: _ClassVar[int]
    PLANNAME_FIELD_NUMBER: _ClassVar[int]
    PLANDESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    EXPIRETIME_FIELD_NUMBER: _ClassVar[int]
    PAYMENTINFO_FIELD_NUMBER: _ClassVar[int]
    success: bool
    balance: float
    planName: str
    planDescription: str
    expireTime: _timestamp_pb2.Timestamp
    paymentInfo: PaymentInfo
    def __init__(self, success: bool = ..., balance: _Optional[float] = ..., planName: _Optional[str] = ..., planDescription: _Optional[str] = ..., expireTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., paymentInfo: _Optional[_Union[PaymentInfo, _Mapping]] = ...) -> None: ...

class Promotion(_message.Message):
    __slots__ = ("id", "cloudName", "title", "subTitle", "rules", "notice", "url")
    ID_FIELD_NUMBER: _ClassVar[int]
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    SUBTITLE_FIELD_NUMBER: _ClassVar[int]
    RULES_FIELD_NUMBER: _ClassVar[int]
    NOTICE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    id: str
    cloudName: str
    title: str
    subTitle: str
    rules: str
    notice: str
    url: str
    def __init__(self, id: _Optional[str] = ..., cloudName: _Optional[str] = ..., title: _Optional[str] = ..., subTitle: _Optional[str] = ..., rules: _Optional[str] = ..., notice: _Optional[str] = ..., url: _Optional[str] = ...) -> None: ...

class GetPromotionsResult(_message.Message):
    __slots__ = ("promotions",)
    PROMOTIONS_FIELD_NUMBER: _ClassVar[int]
    promotions: _containers.RepeatedCompositeFieldContainer[Promotion]
    def __init__(self, promotions: _Optional[_Iterable[_Union[Promotion, _Mapping]]] = ...) -> None: ...

class UpdatePromotionResultByCloudRequest(_message.Message):
    __slots__ = ("cloudName", "cloudAccountId", "promotionId")
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    CLOUDACCOUNTID_FIELD_NUMBER: _ClassVar[int]
    PROMOTIONID_FIELD_NUMBER: _ClassVar[int]
    cloudName: str
    cloudAccountId: str
    promotionId: str
    def __init__(self, cloudName: _Optional[str] = ..., cloudAccountId: _Optional[str] = ..., promotionId: _Optional[str] = ...) -> None: ...

class SendPromotionActionRequest(_message.Message):
    __slots__ = ("cloudName", "cloudAccountId", "promotionId")
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    CLOUDACCOUNTID_FIELD_NUMBER: _ClassVar[int]
    PROMOTIONID_FIELD_NUMBER: _ClassVar[int]
    cloudName: str
    cloudAccountId: str
    promotionId: str
    def __init__(self, cloudName: _Optional[str] = ..., cloudAccountId: _Optional[str] = ..., promotionId: _Optional[str] = ...) -> None: ...

class OfflineStatus(_message.Message):
    __slots__ = ("quota", "total")
    QUOTA_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    quota: int
    total: int
    def __init__(self, quota: _Optional[int] = ..., total: _Optional[int] = ...) -> None: ...

class OfflineFile(_message.Message):
    __slots__ = ("name", "size", "url", "status", "infoHash", "fileId", "add_time", "parentId", "percendDone", "peers")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    INFOHASH_FIELD_NUMBER: _ClassVar[int]
    FILEID_FIELD_NUMBER: _ClassVar[int]
    ADD_TIME_FIELD_NUMBER: _ClassVar[int]
    PARENTID_FIELD_NUMBER: _ClassVar[int]
    PERCENDDONE_FIELD_NUMBER: _ClassVar[int]
    PEERS_FIELD_NUMBER: _ClassVar[int]
    name: str
    size: int
    url: str
    status: OfflineFileStatus
    infoHash: str
    fileId: str
    add_time: int
    parentId: str
    percendDone: float
    peers: int
    def __init__(self, name: _Optional[str] = ..., size: _Optional[int] = ..., url: _Optional[str] = ..., status: _Optional[_Union[OfflineFileStatus, str]] = ..., infoHash: _Optional[str] = ..., fileId: _Optional[str] = ..., add_time: _Optional[int] = ..., parentId: _Optional[str] = ..., percendDone: _Optional[float] = ..., peers: _Optional[int] = ...) -> None: ...

class OfflineFileListAllRequest(_message.Message):
    __slots__ = ("cloudName", "cloudAccountId", "page", "path")
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    CLOUDACCOUNTID_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    cloudName: str
    cloudAccountId: str
    page: int
    path: str
    def __init__(self, cloudName: _Optional[str] = ..., cloudAccountId: _Optional[str] = ..., page: _Optional[int] = ..., path: _Optional[str] = ...) -> None: ...

class OfflineFileListAllResult(_message.Message):
    __slots__ = ("pageNo", "pageRowCount", "pageCount", "totalCount", "status", "offlineFiles")
    PAGENO_FIELD_NUMBER: _ClassVar[int]
    PAGEROWCOUNT_FIELD_NUMBER: _ClassVar[int]
    PAGECOUNT_FIELD_NUMBER: _ClassVar[int]
    TOTALCOUNT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    OFFLINEFILES_FIELD_NUMBER: _ClassVar[int]
    pageNo: int
    pageRowCount: int
    pageCount: int
    totalCount: int
    status: OfflineStatus
    offlineFiles: _containers.RepeatedCompositeFieldContainer[OfflineFile]
    def __init__(self, pageNo: _Optional[int] = ..., pageRowCount: _Optional[int] = ..., pageCount: _Optional[int] = ..., totalCount: _Optional[int] = ..., status: _Optional[_Union[OfflineStatus, _Mapping]] = ..., offlineFiles: _Optional[_Iterable[_Union[OfflineFile, _Mapping]]] = ...) -> None: ...

class OfflineFileListResult(_message.Message):
    __slots__ = ("offlineFiles", "status")
    OFFLINEFILES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    offlineFiles: _containers.RepeatedCompositeFieldContainer[OfflineFile]
    status: OfflineStatus
    def __init__(self, offlineFiles: _Optional[_Iterable[_Union[OfflineFile, _Mapping]]] = ..., status: _Optional[_Union[OfflineStatus, _Mapping]] = ...) -> None: ...

class OfflineQuotaRequest(_message.Message):
    __slots__ = ("cloudName", "cloudAccountId", "path")
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    CLOUDACCOUNTID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    cloudName: str
    cloudAccountId: str
    path: str
    def __init__(self, cloudName: _Optional[str] = ..., cloudAccountId: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class OfflineQuotaInfo(_message.Message):
    __slots__ = ("total", "used", "left")
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    USED_FIELD_NUMBER: _ClassVar[int]
    LEFT_FIELD_NUMBER: _ClassVar[int]
    total: int
    used: int
    left: int
    def __init__(self, total: _Optional[int] = ..., used: _Optional[int] = ..., left: _Optional[int] = ...) -> None: ...

class ClearOfflineFileRequest(_message.Message):
    __slots__ = ("cloudName", "cloudAccountId", "filter", "deleteFiles", "path")
    class Filter(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        All: _ClassVar[ClearOfflineFileRequest.Filter]
        Finished: _ClassVar[ClearOfflineFileRequest.Filter]
        Error: _ClassVar[ClearOfflineFileRequest.Filter]
        Downloading: _ClassVar[ClearOfflineFileRequest.Filter]
    All: ClearOfflineFileRequest.Filter
    Finished: ClearOfflineFileRequest.Filter
    Error: ClearOfflineFileRequest.Filter
    Downloading: ClearOfflineFileRequest.Filter
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    CLOUDACCOUNTID_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    DELETEFILES_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    cloudName: str
    cloudAccountId: str
    filter: ClearOfflineFileRequest.Filter
    deleteFiles: bool
    path: str
    def __init__(self, cloudName: _Optional[str] = ..., cloudAccountId: _Optional[str] = ..., filter: _Optional[_Union[ClearOfflineFileRequest.Filter, str]] = ..., deleteFiles: bool = ..., path: _Optional[str] = ...) -> None: ...

class RestartOfflineFileRequest(_message.Message):
    __slots__ = ("cloudName", "cloudAccountId", "infoHash", "url", "parentId", "path")
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    CLOUDACCOUNTID_FIELD_NUMBER: _ClassVar[int]
    INFOHASH_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    PARENTID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    cloudName: str
    cloudAccountId: str
    infoHash: str
    url: str
    parentId: str
    path: str
    def __init__(self, cloudName: _Optional[str] = ..., cloudAccountId: _Optional[str] = ..., infoHash: _Optional[str] = ..., url: _Optional[str] = ..., parentId: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class BindCloudAccountRequest(_message.Message):
    __slots__ = ("cloudName", "cloudAccountId")
    CLOUDNAME_FIELD_NUMBER: _ClassVar[int]
    CLOUDACCOUNTID_FIELD_NUMBER: _ClassVar[int]
    cloudName: str
    cloudAccountId: str
    def __init__(self, cloudName: _Optional[str] = ..., cloudAccountId: _Optional[str] = ...) -> None: ...

class TransferBalanceRequest(_message.Message):
    __slots__ = ("toUserName", "amount", "password")
    TOUSERNAME_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    toUserName: str
    amount: float
    password: str
    def __init__(self, toUserName: _Optional[str] = ..., amount: _Optional[float] = ..., password: _Optional[str] = ...) -> None: ...

class SendChangeEmailCodeRequest(_message.Message):
    __slots__ = ("newEmail", "password")
    NEWEMAIL_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    newEmail: str
    password: str
    def __init__(self, newEmail: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class ChangeEmailRequest(_message.Message):
    __slots__ = ("newEmail", "password", "changeCode")
    NEWEMAIL_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    CHANGECODE_FIELD_NUMBER: _ClassVar[int]
    newEmail: str
    password: str
    changeCode: str
    def __init__(self, newEmail: _Optional[str] = ..., password: _Optional[str] = ..., changeCode: _Optional[str] = ...) -> None: ...

class ChangeEmailAndPasswordRequest(_message.Message):
    __slots__ = ("newEmail", "newPassword", "syncUserDataWithCloud")
    NEWEMAIL_FIELD_NUMBER: _ClassVar[int]
    NEWPASSWORD_FIELD_NUMBER: _ClassVar[int]
    SYNCUSERDATAWITHCLOUD_FIELD_NUMBER: _ClassVar[int]
    newEmail: str
    newPassword: str
    syncUserDataWithCloud: bool
    def __init__(self, newEmail: _Optional[str] = ..., newPassword: _Optional[str] = ..., syncUserDataWithCloud: bool = ...) -> None: ...

class BalanceLog(_message.Message):
    __slots__ = ("balance_before", "balance_after", "balance_change", "operation", "operation_source", "operation_id", "operation_time")
    class BalancceChangeOperation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Unknown: _ClassVar[BalanceLog.BalancceChangeOperation]
        Deposit: _ClassVar[BalanceLog.BalancceChangeOperation]
        Refund: _ClassVar[BalanceLog.BalancceChangeOperation]
    Unknown: BalanceLog.BalancceChangeOperation
    Deposit: BalanceLog.BalancceChangeOperation
    Refund: BalanceLog.BalancceChangeOperation
    BALANCE_BEFORE_FIELD_NUMBER: _ClassVar[int]
    BALANCE_AFTER_FIELD_NUMBER: _ClassVar[int]
    BALANCE_CHANGE_FIELD_NUMBER: _ClassVar[int]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    OPERATION_SOURCE_FIELD_NUMBER: _ClassVar[int]
    OPERATION_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_TIME_FIELD_NUMBER: _ClassVar[int]
    balance_before: float
    balance_after: float
    balance_change: float
    operation: BalanceLog.BalancceChangeOperation
    operation_source: str
    operation_id: str
    operation_time: _timestamp_pb2.Timestamp
    def __init__(self, balance_before: _Optional[float] = ..., balance_after: _Optional[float] = ..., balance_change: _Optional[float] = ..., operation: _Optional[_Union[BalanceLog.BalancceChangeOperation, str]] = ..., operation_source: _Optional[str] = ..., operation_id: _Optional[str] = ..., operation_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class BalanceLogResult(_message.Message):
    __slots__ = ("logs",)
    LOGS_FIELD_NUMBER: _ClassVar[int]
    logs: _containers.RepeatedCompositeFieldContainer[BalanceLog]
    def __init__(self, logs: _Optional[_Iterable[_Union[BalanceLog, _Mapping]]] = ...) -> None: ...

class CheckFinalPriceRequest(_message.Message):
    __slots__ = ("planId", "couponCode")
    PLANID_FIELD_NUMBER: _ClassVar[int]
    COUPONCODE_FIELD_NUMBER: _ClassVar[int]
    planId: str
    couponCode: str
    def __init__(self, planId: _Optional[str] = ..., couponCode: _Optional[str] = ...) -> None: ...

class CheckFinalPriceResult(_message.Message):
    __slots__ = ("planId", "planPrice", "userBalance", "couponDiscountAmount", "couponError", "finalPrice")
    PLANID_FIELD_NUMBER: _ClassVar[int]
    PLANPRICE_FIELD_NUMBER: _ClassVar[int]
    USERBALANCE_FIELD_NUMBER: _ClassVar[int]
    COUPONDISCOUNTAMOUNT_FIELD_NUMBER: _ClassVar[int]
    COUPONERROR_FIELD_NUMBER: _ClassVar[int]
    FINALPRICE_FIELD_NUMBER: _ClassVar[int]
    planId: str
    planPrice: float
    userBalance: float
    couponDiscountAmount: float
    couponError: str
    finalPrice: float
    def __init__(self, planId: _Optional[str] = ..., planPrice: _Optional[float] = ..., userBalance: _Optional[float] = ..., couponDiscountAmount: _Optional[float] = ..., couponError: _Optional[str] = ..., finalPrice: _Optional[float] = ...) -> None: ...

class CheckActivationCodeResult(_message.Message):
    __slots__ = ("planId", "planName", "planDescription")
    PLANID_FIELD_NUMBER: _ClassVar[int]
    PLANNAME_FIELD_NUMBER: _ClassVar[int]
    PLANDESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    planId: str
    planName: str
    planDescription: str
    def __init__(self, planId: _Optional[str] = ..., planName: _Optional[str] = ..., planDescription: _Optional[str] = ...) -> None: ...

class CheckCouponCodeRequest(_message.Message):
    __slots__ = ("planId", "couponCode")
    PLANID_FIELD_NUMBER: _ClassVar[int]
    COUPONCODE_FIELD_NUMBER: _ClassVar[int]
    planId: str
    couponCode: str
    def __init__(self, planId: _Optional[str] = ..., couponCode: _Optional[str] = ...) -> None: ...

class CouponCodeResult(_message.Message):
    __slots__ = ("couponCode", "couponDescription", "isPercentage", "couponDiscountAmount")
    COUPONCODE_FIELD_NUMBER: _ClassVar[int]
    COUPONDESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ISPERCENTAGE_FIELD_NUMBER: _ClassVar[int]
    COUPONDISCOUNTAMOUNT_FIELD_NUMBER: _ClassVar[int]
    couponCode: str
    couponDescription: str
    isPercentage: bool
    couponDiscountAmount: float
    def __init__(self, couponCode: _Optional[str] = ..., couponDescription: _Optional[str] = ..., isPercentage: bool = ..., couponDiscountAmount: _Optional[float] = ...) -> None: ...

class FileBackupRule(_message.Message):
    __slots__ = ("extensions", "fileNames", "regex", "minSize", "isEnabled", "isBlackList", "applyToFolder", "applyToFile")
    EXTENSIONS_FIELD_NUMBER: _ClassVar[int]
    FILENAMES_FIELD_NUMBER: _ClassVar[int]
    REGEX_FIELD_NUMBER: _ClassVar[int]
    MINSIZE_FIELD_NUMBER: _ClassVar[int]
    ISENABLED_FIELD_NUMBER: _ClassVar[int]
    ISBLACKLIST_FIELD_NUMBER: _ClassVar[int]
    APPLYTOFOLDER_FIELD_NUMBER: _ClassVar[int]
    APPLYTOFILE_FIELD_NUMBER: _ClassVar[int]
    extensions: str
    fileNames: str
    regex: str
    minSize: int
    isEnabled: bool
    isBlackList: bool
    applyToFolder: bool
    applyToFile: bool
    def __init__(self, extensions: _Optional[str] = ..., fileNames: _Optional[str] = ..., regex: _Optional[str] = ..., minSize: _Optional[int] = ..., isEnabled: bool = ..., isBlackList: bool = ..., applyToFolder: bool = ..., applyToFile: bool = ...) -> None: ...

class BackupDestination(_message.Message):
    __slots__ = ("destinationPath", "isEnabled", "lastFinishTime")
    DESTINATIONPATH_FIELD_NUMBER: _ClassVar[int]
    ISENABLED_FIELD_NUMBER: _ClassVar[int]
    LASTFINISHTIME_FIELD_NUMBER: _ClassVar[int]
    destinationPath: str
    isEnabled: bool
    lastFinishTime: _timestamp_pb2.Timestamp
    def __init__(self, destinationPath: _Optional[str] = ..., isEnabled: bool = ..., lastFinishTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class DaysOfWeek(_message.Message):
    __slots__ = ("daysOfWeek",)
    DAYSOFWEEK_FIELD_NUMBER: _ClassVar[int]
    daysOfWeek: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, daysOfWeek: _Optional[_Iterable[int]] = ...) -> None: ...

class TimeSchedule(_message.Message):
    __slots__ = ("isEnabled", "hour", "minute", "second", "daysOfWeek")
    ISENABLED_FIELD_NUMBER: _ClassVar[int]
    HOUR_FIELD_NUMBER: _ClassVar[int]
    MINUTE_FIELD_NUMBER: _ClassVar[int]
    SECOND_FIELD_NUMBER: _ClassVar[int]
    DAYSOFWEEK_FIELD_NUMBER: _ClassVar[int]
    isEnabled: bool
    hour: int
    minute: int
    second: int
    daysOfWeek: DaysOfWeek
    def __init__(self, isEnabled: bool = ..., hour: _Optional[int] = ..., minute: _Optional[int] = ..., second: _Optional[int] = ..., daysOfWeek: _Optional[_Union[DaysOfWeek, _Mapping]] = ...) -> None: ...

class Backup(_message.Message):
    __slots__ = ("sourcePath", "destinations", "fileBackupRules", "fileReplaceRule", "fileDeleteRule", "fileCompletionRule", "isEnabled", "fileSystemWatchEnabled", "walkingThroughIntervalSecs", "forceWalkingThroughOnStart", "timeSchedules", "isTimeSchedulesEnabled")
    SOURCEPATH_FIELD_NUMBER: _ClassVar[int]
    DESTINATIONS_FIELD_NUMBER: _ClassVar[int]
    FILEBACKUPRULES_FIELD_NUMBER: _ClassVar[int]
    FILEREPLACERULE_FIELD_NUMBER: _ClassVar[int]
    FILEDELETERULE_FIELD_NUMBER: _ClassVar[int]
    FILECOMPLETIONRULE_FIELD_NUMBER: _ClassVar[int]
    ISENABLED_FIELD_NUMBER: _ClassVar[int]
    FILESYSTEMWATCHENABLED_FIELD_NUMBER: _ClassVar[int]
    WALKINGTHROUGHINTERVALSECS_FIELD_NUMBER: _ClassVar[int]
    FORCEWALKINGTHROUGHONSTART_FIELD_NUMBER: _ClassVar[int]
    TIMESCHEDULES_FIELD_NUMBER: _ClassVar[int]
    ISTIMESCHEDULESENABLED_FIELD_NUMBER: _ClassVar[int]
    sourcePath: str
    destinations: _containers.RepeatedCompositeFieldContainer[BackupDestination]
    fileBackupRules: _containers.RepeatedCompositeFieldContainer[FileBackupRule]
    fileReplaceRule: FileReplaceRule
    fileDeleteRule: FileDeleteRule
    fileCompletionRule: FileCompletionRule
    isEnabled: bool
    fileSystemWatchEnabled: bool
    walkingThroughIntervalSecs: int
    forceWalkingThroughOnStart: bool
    timeSchedules: _containers.RepeatedCompositeFieldContainer[TimeSchedule]
    isTimeSchedulesEnabled: bool
    def __init__(self, sourcePath: _Optional[str] = ..., destinations: _Optional[_Iterable[_Union[BackupDestination, _Mapping]]] = ..., fileBackupRules: _Optional[_Iterable[_Union[FileBackupRule, _Mapping]]] = ..., fileReplaceRule: _Optional[_Union[FileReplaceRule, str]] = ..., fileDeleteRule: _Optional[_Union[FileDeleteRule, str]] = ..., fileCompletionRule: _Optional[_Union[FileCompletionRule, str]] = ..., isEnabled: bool = ..., fileSystemWatchEnabled: bool = ..., walkingThroughIntervalSecs: _Optional[int] = ..., forceWalkingThroughOnStart: bool = ..., timeSchedules: _Optional[_Iterable[_Union[TimeSchedule, _Mapping]]] = ..., isTimeSchedulesEnabled: bool = ...) -> None: ...

class BackupStatus(_message.Message):
    __slots__ = ("backup", "status", "statusMessage", "watcherStatus", "watcherStatusMessage", "errors")
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Idle: _ClassVar[BackupStatus.Status]
        WalkingThrough: _ClassVar[BackupStatus.Status]
        Error: _ClassVar[BackupStatus.Status]
        Disabled: _ClassVar[BackupStatus.Status]
        Scanned: _ClassVar[BackupStatus.Status]
        Finished: _ClassVar[BackupStatus.Status]
    Idle: BackupStatus.Status
    WalkingThrough: BackupStatus.Status
    Error: BackupStatus.Status
    Disabled: BackupStatus.Status
    Scanned: BackupStatus.Status
    Finished: BackupStatus.Status
    class FileWatchStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        WatcherIdle: _ClassVar[BackupStatus.FileWatchStatus]
        Watching: _ClassVar[BackupStatus.FileWatchStatus]
        WatcherError: _ClassVar[BackupStatus.FileWatchStatus]
        WatcherDisabled: _ClassVar[BackupStatus.FileWatchStatus]
    WatcherIdle: BackupStatus.FileWatchStatus
    Watching: BackupStatus.FileWatchStatus
    WatcherError: BackupStatus.FileWatchStatus
    WatcherDisabled: BackupStatus.FileWatchStatus
    BACKUP_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STATUSMESSAGE_FIELD_NUMBER: _ClassVar[int]
    WATCHERSTATUS_FIELD_NUMBER: _ClassVar[int]
    WATCHERSTATUSMESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    backup: Backup
    status: BackupStatus.Status
    statusMessage: str
    watcherStatus: BackupStatus.FileWatchStatus
    watcherStatusMessage: str
    errors: _containers.RepeatedCompositeFieldContainer[TaskError]
    def __init__(self, backup: _Optional[_Union[Backup, _Mapping]] = ..., status: _Optional[_Union[BackupStatus.Status, str]] = ..., statusMessage: _Optional[str] = ..., watcherStatus: _Optional[_Union[BackupStatus.FileWatchStatus, str]] = ..., watcherStatusMessage: _Optional[str] = ..., errors: _Optional[_Iterable[_Union[TaskError, _Mapping]]] = ...) -> None: ...

class BackupList(_message.Message):
    __slots__ = ("backups",)
    BACKUPS_FIELD_NUMBER: _ClassVar[int]
    backups: _containers.RepeatedCompositeFieldContainer[BackupStatus]
    def __init__(self, backups: _Optional[_Iterable[_Union[BackupStatus, _Mapping]]] = ...) -> None: ...

class BackupModifyRequest(_message.Message):
    __slots__ = ("sourcePath", "destinations", "fileBackupRules", "fileReplaceRule", "fileDeleteRule", "fileSystemWatchEnabled", "walkingThroughIntervalSecs")
    SOURCEPATH_FIELD_NUMBER: _ClassVar[int]
    DESTINATIONS_FIELD_NUMBER: _ClassVar[int]
    FILEBACKUPRULES_FIELD_NUMBER: _ClassVar[int]
    FILEREPLACERULE_FIELD_NUMBER: _ClassVar[int]
    FILEDELETERULE_FIELD_NUMBER: _ClassVar[int]
    FILESYSTEMWATCHENABLED_FIELD_NUMBER: _ClassVar[int]
    WALKINGTHROUGHINTERVALSECS_FIELD_NUMBER: _ClassVar[int]
    sourcePath: str
    destinations: _containers.RepeatedCompositeFieldContainer[BackupDestination]
    fileBackupRules: _containers.RepeatedCompositeFieldContainer[FileBackupRule]
    fileReplaceRule: FileReplaceRule
    fileDeleteRule: FileDeleteRule
    fileSystemWatchEnabled: bool
    walkingThroughIntervalSecs: int
    def __init__(self, sourcePath: _Optional[str] = ..., destinations: _Optional[_Iterable[_Union[BackupDestination, _Mapping]]] = ..., fileBackupRules: _Optional[_Iterable[_Union[FileBackupRule, _Mapping]]] = ..., fileReplaceRule: _Optional[_Union[FileReplaceRule, str]] = ..., fileDeleteRule: _Optional[_Union[FileDeleteRule, str]] = ..., fileSystemWatchEnabled: bool = ..., walkingThroughIntervalSecs: _Optional[int] = ...) -> None: ...

class BackupSetEnabledRequest(_message.Message):
    __slots__ = ("sourcePath", "isEnabled")
    SOURCEPATH_FIELD_NUMBER: _ClassVar[int]
    ISENABLED_FIELD_NUMBER: _ClassVar[int]
    sourcePath: str
    isEnabled: bool
    def __init__(self, sourcePath: _Optional[str] = ..., isEnabled: bool = ...) -> None: ...

class Device(_message.Message):
    __slots__ = ("deviceId", "deviceName", "osType", "version", "ipAddress", "lastUpdateTime")
    DEVICEID_FIELD_NUMBER: _ClassVar[int]
    DEVICENAME_FIELD_NUMBER: _ClassVar[int]
    OSTYPE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    IPADDRESS_FIELD_NUMBER: _ClassVar[int]
    LASTUPDATETIME_FIELD_NUMBER: _ClassVar[int]
    deviceId: str
    deviceName: str
    osType: str
    version: str
    ipAddress: str
    lastUpdateTime: _timestamp_pb2.Timestamp
    def __init__(self, deviceId: _Optional[str] = ..., deviceName: _Optional[str] = ..., osType: _Optional[str] = ..., version: _Optional[str] = ..., ipAddress: _Optional[str] = ..., lastUpdateTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class OnlineDevices(_message.Message):
    __slots__ = ("devices",)
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    devices: _containers.RepeatedCompositeFieldContainer[Device]
    def __init__(self, devices: _Optional[_Iterable[_Union[Device, _Mapping]]] = ...) -> None: ...

class DeviceRequest(_message.Message):
    __slots__ = ("deviceId",)
    DEVICEID_FIELD_NUMBER: _ClassVar[int]
    deviceId: str
    def __init__(self, deviceId: _Optional[str] = ...) -> None: ...

class LogFileRecord(_message.Message):
    __slots__ = ("fileName", "lastModifiedTime", "fileSize", "signature")
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    LASTMODIFIEDTIME_FIELD_NUMBER: _ClassVar[int]
    FILESIZE_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    fileName: str
    lastModifiedTime: _timestamp_pb2.Timestamp
    fileSize: int
    signature: str
    def __init__(self, fileName: _Optional[str] = ..., lastModifiedTime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., fileSize: _Optional[int] = ..., signature: _Optional[str] = ...) -> None: ...

class ListLogFileResult(_message.Message):
    __slots__ = ("logFiles",)
    LOGFILES_FIELD_NUMBER: _ClassVar[int]
    logFiles: _containers.RepeatedCompositeFieldContainer[LogFileRecord]
    def __init__(self, logFiles: _Optional[_Iterable[_Union[LogFileRecord, _Mapping]]] = ...) -> None: ...

class FileSystemChangeStatistics(_message.Message):
    __slots__ = ("createCount", "deleteCount", "renameCount")
    CREATECOUNT_FIELD_NUMBER: _ClassVar[int]
    DELETECOUNT_FIELD_NUMBER: _ClassVar[int]
    RENAMECOUNT_FIELD_NUMBER: _ClassVar[int]
    createCount: int
    deleteCount: int
    renameCount: int
    def __init__(self, createCount: _Optional[int] = ..., deleteCount: _Optional[int] = ..., renameCount: _Optional[int] = ...) -> None: ...

class WalkThroughFolderResult(_message.Message):
    __slots__ = ("totalFolderCount", "totalFileCount", "totalSize")
    TOTALFOLDERCOUNT_FIELD_NUMBER: _ClassVar[int]
    TOTALFILECOUNT_FIELD_NUMBER: _ClassVar[int]
    TOTALSIZE_FIELD_NUMBER: _ClassVar[int]
    totalFolderCount: int
    totalFileCount: int
    totalSize: int
    def __init__(self, totalFolderCount: _Optional[int] = ..., totalFileCount: _Optional[int] = ..., totalSize: _Optional[int] = ...) -> None: ...

class WebhookRequest(_message.Message):
    __slots__ = ("fileName", "content")
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    fileName: str
    content: str
    def __init__(self, fileName: _Optional[str] = ..., content: _Optional[str] = ...) -> None: ...

class WebhookInfo(_message.Message):
    __slots__ = ("fileName", "content", "isValid")
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    ISVALID_FIELD_NUMBER: _ClassVar[int]
    fileName: str
    content: str
    isValid: bool
    def __init__(self, fileName: _Optional[str] = ..., content: _Optional[str] = ..., isValid: bool = ...) -> None: ...

class WebhookList(_message.Message):
    __slots__ = ("webhooks",)
    WEBHOOKS_FIELD_NUMBER: _ClassVar[int]
    webhooks: _containers.RepeatedCompositeFieldContainer[WebhookInfo]
    def __init__(self, webhooks: _Optional[_Iterable[_Union[WebhookInfo, _Mapping]]] = ...) -> None: ...

class AddDavUserRequest(_message.Message):
    __slots__ = ("userName", "password", "rootPath", "readOnly", "enabled", "guest")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    ROOTPATH_FIELD_NUMBER: _ClassVar[int]
    READONLY_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    GUEST_FIELD_NUMBER: _ClassVar[int]
    userName: str
    password: str
    rootPath: str
    readOnly: bool
    enabled: bool
    guest: bool
    def __init__(self, userName: _Optional[str] = ..., password: _Optional[str] = ..., rootPath: _Optional[str] = ..., readOnly: bool = ..., enabled: bool = ..., guest: bool = ...) -> None: ...

class ModifyDavUserRequest(_message.Message):
    __slots__ = ("userName", "password", "rootPath", "readOnly", "enabled", "guest")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    ROOTPATH_FIELD_NUMBER: _ClassVar[int]
    READONLY_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    GUEST_FIELD_NUMBER: _ClassVar[int]
    userName: str
    password: str
    rootPath: str
    readOnly: bool
    enabled: bool
    guest: bool
    def __init__(self, userName: _Optional[str] = ..., password: _Optional[str] = ..., rootPath: _Optional[str] = ..., readOnly: bool = ..., enabled: bool = ..., guest: bool = ...) -> None: ...

class DavUser(_message.Message):
    __slots__ = ("userName", "password", "rootPath", "readOnly", "enabled", "guest")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    ROOTPATH_FIELD_NUMBER: _ClassVar[int]
    READONLY_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    GUEST_FIELD_NUMBER: _ClassVar[int]
    userName: str
    password: str
    rootPath: str
    readOnly: bool
    enabled: bool
    guest: bool
    def __init__(self, userName: _Optional[str] = ..., password: _Optional[str] = ..., rootPath: _Optional[str] = ..., readOnly: bool = ..., enabled: bool = ..., guest: bool = ...) -> None: ...

class DavServerConfig(_message.Message):
    __slots__ = ("davServerEnabled", "davServerPath", "enableClouddriveAccount", "clouddriveAccountRootPath", "clouddriveAccountReadOnly", "enableAnonymousAccess", "anonymousRootPath", "anonymousReadOnly", "users", "enableAccessLog")
    DAVSERVERENABLED_FIELD_NUMBER: _ClassVar[int]
    DAVSERVERPATH_FIELD_NUMBER: _ClassVar[int]
    ENABLECLOUDDRIVEACCOUNT_FIELD_NUMBER: _ClassVar[int]
    CLOUDDRIVEACCOUNTROOTPATH_FIELD_NUMBER: _ClassVar[int]
    CLOUDDRIVEACCOUNTREADONLY_FIELD_NUMBER: _ClassVar[int]
    ENABLEANONYMOUSACCESS_FIELD_NUMBER: _ClassVar[int]
    ANONYMOUSROOTPATH_FIELD_NUMBER: _ClassVar[int]
    ANONYMOUSREADONLY_FIELD_NUMBER: _ClassVar[int]
    USERS_FIELD_NUMBER: _ClassVar[int]
    ENABLEACCESSLOG_FIELD_NUMBER: _ClassVar[int]
    davServerEnabled: bool
    davServerPath: str
    enableClouddriveAccount: bool
    clouddriveAccountRootPath: str
    clouddriveAccountReadOnly: bool
    enableAnonymousAccess: bool
    anonymousRootPath: str
    anonymousReadOnly: bool
    users: _containers.RepeatedCompositeFieldContainer[DavUser]
    enableAccessLog: bool
    def __init__(self, davServerEnabled: bool = ..., davServerPath: _Optional[str] = ..., enableClouddriveAccount: bool = ..., clouddriveAccountRootPath: _Optional[str] = ..., clouddriveAccountReadOnly: bool = ..., enableAnonymousAccess: bool = ..., anonymousRootPath: _Optional[str] = ..., anonymousReadOnly: bool = ..., users: _Optional[_Iterable[_Union[DavUser, _Mapping]]] = ..., enableAccessLog: bool = ...) -> None: ...

class ModifyDavServerConfigRequest(_message.Message):
    __slots__ = ("enableDavServer", "enableClouddriveAccount", "clouddriveAccountRootPath", "clouddriveAccountReadOnly", "enableAnonymousAccess", "anonymousRootPath", "anonymousReadOnly", "enableAccessLog")
    ENABLEDAVSERVER_FIELD_NUMBER: _ClassVar[int]
    ENABLECLOUDDRIVEACCOUNT_FIELD_NUMBER: _ClassVar[int]
    CLOUDDRIVEACCOUNTROOTPATH_FIELD_NUMBER: _ClassVar[int]
    CLOUDDRIVEACCOUNTREADONLY_FIELD_NUMBER: _ClassVar[int]
    ENABLEANONYMOUSACCESS_FIELD_NUMBER: _ClassVar[int]
    ANONYMOUSROOTPATH_FIELD_NUMBER: _ClassVar[int]
    ANONYMOUSREADONLY_FIELD_NUMBER: _ClassVar[int]
    ENABLEACCESSLOG_FIELD_NUMBER: _ClassVar[int]
    enableDavServer: bool
    enableClouddriveAccount: bool
    clouddriveAccountRootPath: str
    clouddriveAccountReadOnly: bool
    enableAnonymousAccess: bool
    anonymousRootPath: str
    anonymousReadOnly: bool
    enableAccessLog: bool
    def __init__(self, enableDavServer: bool = ..., enableClouddriveAccount: bool = ..., clouddriveAccountRootPath: _Optional[str] = ..., clouddriveAccountReadOnly: bool = ..., enableAnonymousAccess: bool = ..., anonymousRootPath: _Optional[str] = ..., anonymousReadOnly: bool = ..., enableAccessLog: bool = ...) -> None: ...

class RemoteUploadChannelRequest(_message.Message):
    __slots__ = ("device_id",)
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    def __init__(self, device_id: _Optional[str] = ...) -> None: ...

class RemoteUploadChannelReply(_message.Message):
    __slots__ = ("upload_id", "read_data", "hash_data", "status_changed")
    UPLOAD_ID_FIELD_NUMBER: _ClassVar[int]
    READ_DATA_FIELD_NUMBER: _ClassVar[int]
    HASH_DATA_FIELD_NUMBER: _ClassVar[int]
    STATUS_CHANGED_FIELD_NUMBER: _ClassVar[int]
    upload_id: str
    read_data: RemoteReadDataRequest
    hash_data: RemoteHashDataRequest
    status_changed: RemoteUploadStatusChanged
    def __init__(self, upload_id: _Optional[str] = ..., read_data: _Optional[_Union[RemoteReadDataRequest, _Mapping]] = ..., hash_data: _Optional[_Union[RemoteHashDataRequest, _Mapping]] = ..., status_changed: _Optional[_Union[RemoteUploadStatusChanged, _Mapping]] = ...) -> None: ...

class RemoteUploadControlRequest(_message.Message):
    __slots__ = ("upload_id", "cancel", "pause", "resume")
    UPLOAD_ID_FIELD_NUMBER: _ClassVar[int]
    CANCEL_FIELD_NUMBER: _ClassVar[int]
    PAUSE_FIELD_NUMBER: _ClassVar[int]
    RESUME_FIELD_NUMBER: _ClassVar[int]
    upload_id: str
    cancel: CancelRemoteUpload
    pause: PauseRemoteUpload
    resume: ResumeRemoteUpload
    def __init__(self, upload_id: _Optional[str] = ..., cancel: _Optional[_Union[CancelRemoteUpload, _Mapping]] = ..., pause: _Optional[_Union[PauseRemoteUpload, _Mapping]] = ..., resume: _Optional[_Union[ResumeRemoteUpload, _Mapping]] = ...) -> None: ...

class StartRemoteUploadRequest(_message.Message):
    __slots__ = ("file_path", "file_size", "known_hashes", "client_can_calculate_hashes")
    class KnownHashesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: str
        def __init__(self, key: _Optional[int] = ..., value: _Optional[str] = ...) -> None: ...
    FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    FILE_SIZE_FIELD_NUMBER: _ClassVar[int]
    KNOWN_HASHES_FIELD_NUMBER: _ClassVar[int]
    CLIENT_CAN_CALCULATE_HASHES_FIELD_NUMBER: _ClassVar[int]
    file_path: str
    file_size: int
    known_hashes: _containers.ScalarMap[int, str]
    client_can_calculate_hashes: bool
    def __init__(self, file_path: _Optional[str] = ..., file_size: _Optional[int] = ..., known_hashes: _Optional[_Mapping[int, str]] = ..., client_can_calculate_hashes: bool = ...) -> None: ...

class CancelRemoteUpload(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RemoteUploadStarted(_message.Message):
    __slots__ = ("upload_id",)
    UPLOAD_ID_FIELD_NUMBER: _ClassVar[int]
    upload_id: str
    def __init__(self, upload_id: _Optional[str] = ...) -> None: ...

class RemoteUploadProgress(_message.Message):
    __slots__ = ("bytes_uploaded", "total_bytes")
    BYTES_UPLOADED_FIELD_NUMBER: _ClassVar[int]
    TOTAL_BYTES_FIELD_NUMBER: _ClassVar[int]
    bytes_uploaded: int
    total_bytes: int
    def __init__(self, bytes_uploaded: _Optional[int] = ..., total_bytes: _Optional[int] = ...) -> None: ...

class RemoteRapidUploadCompleted(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RemoteUploadCompleted(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RemoteUploadFailed(_message.Message):
    __slots__ = ("error_message",)
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    error_message: str
    def __init__(self, error_message: _Optional[str] = ...) -> None: ...

class RemoteReadDataRequest(_message.Message):
    __slots__ = ("offset", "length", "lazy_read")
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    LAZY_READ_FIELD_NUMBER: _ClassVar[int]
    offset: int
    length: int
    lazy_read: bool
    def __init__(self, offset: _Optional[int] = ..., length: _Optional[int] = ..., lazy_read: bool = ...) -> None: ...

class RemoteReadDataUpload(_message.Message):
    __slots__ = ("upload_id", "offset", "length", "lazy_read", "data", "is_last_chunk")
    UPLOAD_ID_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    LAZY_READ_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    IS_LAST_CHUNK_FIELD_NUMBER: _ClassVar[int]
    upload_id: str
    offset: int
    length: int
    lazy_read: bool
    data: bytes
    is_last_chunk: bool
    def __init__(self, upload_id: _Optional[str] = ..., offset: _Optional[int] = ..., length: _Optional[int] = ..., lazy_read: bool = ..., data: _Optional[bytes] = ..., is_last_chunk: bool = ...) -> None: ...

class RemoteReadDataReply(_message.Message):
    __slots__ = ("success", "error_message", "bytes_received", "is_last_chunk")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    BYTES_RECEIVED_FIELD_NUMBER: _ClassVar[int]
    IS_LAST_CHUNK_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error_message: str
    bytes_received: int
    is_last_chunk: bool
    def __init__(self, success: bool = ..., error_message: _Optional[str] = ..., bytes_received: _Optional[int] = ..., is_last_chunk: bool = ...) -> None: ...

class RemoteHashDataRequest(_message.Message):
    __slots__ = ("hash_type", "block_size")
    HASH_TYPE_FIELD_NUMBER: _ClassVar[int]
    BLOCK_SIZE_FIELD_NUMBER: _ClassVar[int]
    hash_type: int
    block_size: int
    def __init__(self, hash_type: _Optional[int] = ..., block_size: _Optional[int] = ...) -> None: ...

class RemoteUploadStatusChanged(_message.Message):
    __slots__ = ("status", "error_message")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: UploadFileInfo.Status
    error_message: str
    def __init__(self, status: _Optional[_Union[UploadFileInfo.Status, str]] = ..., error_message: _Optional[str] = ...) -> None: ...

class PauseRemoteUpload(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResumeRemoteUpload(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RemoteHashProgressUpload(_message.Message):
    __slots__ = ("upload_id", "bytes_hashed", "total_bytes", "hash_type", "hash_value", "block_hashes")
    UPLOAD_ID_FIELD_NUMBER: _ClassVar[int]
    BYTES_HASHED_FIELD_NUMBER: _ClassVar[int]
    TOTAL_BYTES_FIELD_NUMBER: _ClassVar[int]
    HASH_TYPE_FIELD_NUMBER: _ClassVar[int]
    HASH_VALUE_FIELD_NUMBER: _ClassVar[int]
    BLOCK_HASHES_FIELD_NUMBER: _ClassVar[int]
    upload_id: str
    bytes_hashed: int
    total_bytes: int
    hash_type: CloudDriveFile.HashType
    hash_value: str
    block_hashes: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, upload_id: _Optional[str] = ..., bytes_hashed: _Optional[int] = ..., total_bytes: _Optional[int] = ..., hash_type: _Optional[_Union[CloudDriveFile.HashType, str]] = ..., hash_value: _Optional[str] = ..., block_hashes: _Optional[_Iterable[str]] = ...) -> None: ...

class RemoteHashProgressReply(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TokenPermissions(_message.Message):
    __slots__ = ("allow_list", "allow_search", "allow_list_local", "allow_create_folder", "allow_create_file", "allow_write", "allow_read", "allow_rename", "allow_move", "allow_copy", "allow_delete", "allow_delete_permanently", "allow_create_encrypt", "allow_unlock_encrypted", "allow_lock_encrypted", "allow_add_offline_download", "allow_list_offline_downloads", "allow_modify_offline_downloads", "allow_shared_links", "allow_view_properties", "allow_get_space_info", "allow_view_runtime_info", "allow_push_message", "allow_get_memberships", "allow_modify_memberships", "allow_get_mounts", "allow_modify_mounts", "allow_get_transfer_tasks", "allow_modify_transfer_tasks", "allow_get_cloud_apis", "allow_modify_cloud_apis", "allow_get_system_settings", "allow_modify_system_settings", "allow_get_backups", "allow_modify_backups", "allow_get_dav_config", "allow_modify_dav_config", "allow_token_management", "allow_get_account_info", "allow_modify_account", "allow_service_control")
    ALLOW_LIST_FIELD_NUMBER: _ClassVar[int]
    ALLOW_SEARCH_FIELD_NUMBER: _ClassVar[int]
    ALLOW_LIST_LOCAL_FIELD_NUMBER: _ClassVar[int]
    ALLOW_CREATE_FOLDER_FIELD_NUMBER: _ClassVar[int]
    ALLOW_CREATE_FILE_FIELD_NUMBER: _ClassVar[int]
    ALLOW_WRITE_FIELD_NUMBER: _ClassVar[int]
    ALLOW_READ_FIELD_NUMBER: _ClassVar[int]
    ALLOW_RENAME_FIELD_NUMBER: _ClassVar[int]
    ALLOW_MOVE_FIELD_NUMBER: _ClassVar[int]
    ALLOW_COPY_FIELD_NUMBER: _ClassVar[int]
    ALLOW_DELETE_FIELD_NUMBER: _ClassVar[int]
    ALLOW_DELETE_PERMANENTLY_FIELD_NUMBER: _ClassVar[int]
    ALLOW_CREATE_ENCRYPT_FIELD_NUMBER: _ClassVar[int]
    ALLOW_UNLOCK_ENCRYPTED_FIELD_NUMBER: _ClassVar[int]
    ALLOW_LOCK_ENCRYPTED_FIELD_NUMBER: _ClassVar[int]
    ALLOW_ADD_OFFLINE_DOWNLOAD_FIELD_NUMBER: _ClassVar[int]
    ALLOW_LIST_OFFLINE_DOWNLOADS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_MODIFY_OFFLINE_DOWNLOADS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_SHARED_LINKS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_VIEW_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    ALLOW_GET_SPACE_INFO_FIELD_NUMBER: _ClassVar[int]
    ALLOW_VIEW_RUNTIME_INFO_FIELD_NUMBER: _ClassVar[int]
    ALLOW_PUSH_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ALLOW_GET_MEMBERSHIPS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_MODIFY_MEMBERSHIPS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_GET_MOUNTS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_MODIFY_MOUNTS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_GET_TRANSFER_TASKS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_MODIFY_TRANSFER_TASKS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_GET_CLOUD_APIS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_MODIFY_CLOUD_APIS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_GET_SYSTEM_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_MODIFY_SYSTEM_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_GET_BACKUPS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_MODIFY_BACKUPS_FIELD_NUMBER: _ClassVar[int]
    ALLOW_GET_DAV_CONFIG_FIELD_NUMBER: _ClassVar[int]
    ALLOW_MODIFY_DAV_CONFIG_FIELD_NUMBER: _ClassVar[int]
    ALLOW_TOKEN_MANAGEMENT_FIELD_NUMBER: _ClassVar[int]
    ALLOW_GET_ACCOUNT_INFO_FIELD_NUMBER: _ClassVar[int]
    ALLOW_MODIFY_ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    ALLOW_SERVICE_CONTROL_FIELD_NUMBER: _ClassVar[int]
    allow_list: bool
    allow_search: bool
    allow_list_local: bool
    allow_create_folder: bool
    allow_create_file: bool
    allow_write: bool
    allow_read: bool
    allow_rename: bool
    allow_move: bool
    allow_copy: bool
    allow_delete: bool
    allow_delete_permanently: bool
    allow_create_encrypt: bool
    allow_unlock_encrypted: bool
    allow_lock_encrypted: bool
    allow_add_offline_download: bool
    allow_list_offline_downloads: bool
    allow_modify_offline_downloads: bool
    allow_shared_links: bool
    allow_view_properties: bool
    allow_get_space_info: bool
    allow_view_runtime_info: bool
    allow_push_message: bool
    allow_get_memberships: bool
    allow_modify_memberships: bool
    allow_get_mounts: bool
    allow_modify_mounts: bool
    allow_get_transfer_tasks: bool
    allow_modify_transfer_tasks: bool
    allow_get_cloud_apis: bool
    allow_modify_cloud_apis: bool
    allow_get_system_settings: bool
    allow_modify_system_settings: bool
    allow_get_backups: bool
    allow_modify_backups: bool
    allow_get_dav_config: bool
    allow_modify_dav_config: bool
    allow_token_management: bool
    allow_get_account_info: bool
    allow_modify_account: bool
    allow_service_control: bool
    def __init__(self, allow_list: bool = ..., allow_search: bool = ..., allow_list_local: bool = ..., allow_create_folder: bool = ..., allow_create_file: bool = ..., allow_write: bool = ..., allow_read: bool = ..., allow_rename: bool = ..., allow_move: bool = ..., allow_copy: bool = ..., allow_delete: bool = ..., allow_delete_permanently: bool = ..., allow_create_encrypt: bool = ..., allow_unlock_encrypted: bool = ..., allow_lock_encrypted: bool = ..., allow_add_offline_download: bool = ..., allow_list_offline_downloads: bool = ..., allow_modify_offline_downloads: bool = ..., allow_shared_links: bool = ..., allow_view_properties: bool = ..., allow_get_space_info: bool = ..., allow_view_runtime_info: bool = ..., allow_push_message: bool = ..., allow_get_memberships: bool = ..., allow_modify_memberships: bool = ..., allow_get_mounts: bool = ..., allow_modify_mounts: bool = ..., allow_get_transfer_tasks: bool = ..., allow_modify_transfer_tasks: bool = ..., allow_get_cloud_apis: bool = ..., allow_modify_cloud_apis: bool = ..., allow_get_system_settings: bool = ..., allow_modify_system_settings: bool = ..., allow_get_backups: bool = ..., allow_modify_backups: bool = ..., allow_get_dav_config: bool = ..., allow_modify_dav_config: bool = ..., allow_token_management: bool = ..., allow_get_account_info: bool = ..., allow_modify_account: bool = ..., allow_service_control: bool = ...) -> None: ...

class TokenInfo(_message.Message):
    __slots__ = ("token", "rootDir", "permissions", "expires_in", "friendly_name", "enableGrpcLog", "enableStreamFileLog")
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    ROOTDIR_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    FRIENDLY_NAME_FIELD_NUMBER: _ClassVar[int]
    ENABLEGRPCLOG_FIELD_NUMBER: _ClassVar[int]
    ENABLESTREAMFILELOG_FIELD_NUMBER: _ClassVar[int]
    token: str
    rootDir: str
    permissions: TokenPermissions
    expires_in: int
    friendly_name: str
    enableGrpcLog: bool
    enableStreamFileLog: bool
    def __init__(self, token: _Optional[str] = ..., rootDir: _Optional[str] = ..., permissions: _Optional[_Union[TokenPermissions, _Mapping]] = ..., expires_in: _Optional[int] = ..., friendly_name: _Optional[str] = ..., enableGrpcLog: bool = ..., enableStreamFileLog: bool = ...) -> None: ...

class CreateTokenRequest(_message.Message):
    __slots__ = ("rootDir", "permissions", "friendly_name", "expires_in", "enableGrpcLog", "enableStreamFileLog")
    ROOTDIR_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    FRIENDLY_NAME_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    ENABLEGRPCLOG_FIELD_NUMBER: _ClassVar[int]
    ENABLESTREAMFILELOG_FIELD_NUMBER: _ClassVar[int]
    rootDir: str
    permissions: TokenPermissions
    friendly_name: str
    expires_in: int
    enableGrpcLog: bool
    enableStreamFileLog: bool
    def __init__(self, rootDir: _Optional[str] = ..., permissions: _Optional[_Union[TokenPermissions, _Mapping]] = ..., friendly_name: _Optional[str] = ..., expires_in: _Optional[int] = ..., enableGrpcLog: bool = ..., enableStreamFileLog: bool = ...) -> None: ...

class ModifyTokenRequest(_message.Message):
    __slots__ = ("token", "rootDir", "permissions", "friendly_name", "expires_in", "enableGrpcLog", "enableStreamFileLog")
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    ROOTDIR_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    FRIENDLY_NAME_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    ENABLEGRPCLOG_FIELD_NUMBER: _ClassVar[int]
    ENABLESTREAMFILELOG_FIELD_NUMBER: _ClassVar[int]
    token: str
    rootDir: str
    permissions: TokenPermissions
    friendly_name: str
    expires_in: int
    enableGrpcLog: bool
    enableStreamFileLog: bool
    def __init__(self, token: _Optional[str] = ..., rootDir: _Optional[str] = ..., permissions: _Optional[_Union[TokenPermissions, _Mapping]] = ..., friendly_name: _Optional[str] = ..., expires_in: _Optional[int] = ..., enableGrpcLog: bool = ..., enableStreamFileLog: bool = ...) -> None: ...

class ListTokensResult(_message.Message):
    __slots__ = ("tokens",)
    TOKENS_FIELD_NUMBER: _ClassVar[int]
    tokens: _containers.RepeatedCompositeFieldContainer[TokenInfo]
    def __init__(self, tokens: _Optional[_Iterable[_Union[TokenInfo, _Mapping]]] = ...) -> None: ...

class WebServerConfig(_message.Message):
    __slots__ = ("http_port", "https_port", "cert_file", "key_file", "enable_https")
    HTTP_PORT_FIELD_NUMBER: _ClassVar[int]
    HTTPS_PORT_FIELD_NUMBER: _ClassVar[int]
    CERT_FILE_FIELD_NUMBER: _ClassVar[int]
    KEY_FILE_FIELD_NUMBER: _ClassVar[int]
    ENABLE_HTTPS_FIELD_NUMBER: _ClassVar[int]
    http_port: int
    https_port: int
    cert_file: str
    key_file: str
    enable_https: bool
    def __init__(self, http_port: _Optional[int] = ..., https_port: _Optional[int] = ..., cert_file: _Optional[str] = ..., key_file: _Optional[str] = ..., enable_https: bool = ...) -> None: ...

class SetWebServerConfigRequest(_message.Message):
    __slots__ = ("http_port", "https_port", "cert_file", "key_file", "enable_https", "cert_content", "key_content")
    HTTP_PORT_FIELD_NUMBER: _ClassVar[int]
    HTTPS_PORT_FIELD_NUMBER: _ClassVar[int]
    CERT_FILE_FIELD_NUMBER: _ClassVar[int]
    KEY_FILE_FIELD_NUMBER: _ClassVar[int]
    ENABLE_HTTPS_FIELD_NUMBER: _ClassVar[int]
    CERT_CONTENT_FIELD_NUMBER: _ClassVar[int]
    KEY_CONTENT_FIELD_NUMBER: _ClassVar[int]
    http_port: int
    https_port: int
    cert_file: str
    key_file: str
    enable_https: bool
    cert_content: str
    key_content: str
    def __init__(self, http_port: _Optional[int] = ..., https_port: _Optional[int] = ..., cert_file: _Optional[str] = ..., key_file: _Optional[str] = ..., enable_https: bool = ..., cert_content: _Optional[str] = ..., key_content: _Optional[str] = ...) -> None: ...

class GenerateSelfSignedCertRequest(_message.Message):
    __slots__ = ("restart_servers",)
    RESTART_SERVERS_FIELD_NUMBER: _ClassVar[int]
    restart_servers: bool
    def __init__(self, restart_servers: bool = ...) -> None: ...
