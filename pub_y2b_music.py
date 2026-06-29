"""YouTube music publisher.

YouTube Studio does not accept public audio-only channel uploads through the
normal creator upload form, so LazyEdit packages music as an art-track MP4
(`youtube_music_video_filename`) and this publisher uploads that video with
music-specific metadata.
"""

from __future__ import annotations

from pub_y2b import YouTubePublisher, remove_non_bmp


class YouTubeMusicPublisher(YouTubePublisher):
    def __init__(self, driver, video_path, thumbnail_path, metadata, test=False):
        normalized = self._normalize_metadata(metadata or {})
        super().__init__(driver, video_path, thumbnail_path, normalized, test)

    @staticmethod
    def _normalize_metadata(metadata: dict) -> dict:
        title = (
            metadata.get("song_title")
            or metadata.get("music_title")
            or metadata.get("title")
            or "Musia song"
        )
        story = (
            metadata.get("long_description")
            or metadata.get("music_story")
            or metadata.get("story")
            or metadata.get("brief_description")
            or ""
        )
        lyrics = metadata.get("lyrics") or metadata.get("song_lyrics") or ""
        artist = metadata.get("artist") or metadata.get("author") or "Musia 慕莎"
        genre = metadata.get("genre") or ""
        language = metadata.get("language") or ""
        source_url = metadata.get("source_url") or metadata.get("canonical_url") or metadata.get("website_url") or ""

        description_parts = [
            story,
            f"Artist: {artist}",
            f"Language: {language}" if language else "",
            f"Genre: {genre}" if genre else "",
            f"Source: {source_url}" if source_url else "",
            "Lyrics:",
            lyrics,
        ]
        description = "\n\n".join(part for part in description_parts if str(part).strip())

        tags = metadata.get("tags")
        if not isinstance(tags, list):
            tags = []
        tags = [
            str(tag).strip()
            for tag in [
                *tags,
                "Musia",
                "LazyingArt",
                "AI music",
                str(artist),
                str(genre),
                str(language),
            ]
            if str(tag).strip()
        ]
        deduped_tags = []
        for tag in tags:
            if tag not in deduped_tags:
                deduped_tags.append(tag)

        output = dict(metadata)
        output["title"] = str(title)
        output["long_description"] = description
        output["brief_description"] = metadata.get("brief_description") or story
        output["middle_description"] = metadata.get("middle_description") or story
        output["tags"] = deduped_tags[:20]
        output["youtube_playlist"] = metadata.get("youtube_playlist") or "Musia"
        return output

    def create_video_title_with_limited_tags(self, metadata):
        title = remove_non_bmp(str(metadata.get("title") or "Musia song"))
        return title[:100]

    def set_playlist(self):
        self.metadata["playlist_name"] = self.metadata.get("youtube_playlist") or self.metadata.get("playlist_name") or "Musia"
        return super().set_playlist()
