from wj_music.domain.similar import AlbumProfile, rank_similar


def profile(
    album_id: int,
    *,
    title: str | None = None,
    year: int | None = None,
    genres: tuple[str, ...] = (),
    labels: tuple[str, ...] = (),
    composers: tuple[str, ...] = (),
) -> AlbumProfile:
    return AlbumProfile(
        album_id=album_id,
        title=title or f"Album {album_id}",
        year=year,
        genres=frozenset(genres),
        labels=frozenset(labels),
        composers=frozenset(composers),
    )


def ids(ranked: list) -> list[int]:  # type: ignore[type-arg]
    return [item.album_id for item in ranked]


class TestScoring:
    def test_never_includes_the_album_itself(self) -> None:
        target = profile(1, genres=("Rock",))

        assert rank_similar(target, [target]) == []

    def test_shared_genres_are_the_strongest_signal(self) -> None:
        target = profile(1, genres=("Rock", "Pop"), labels=("EMI",))
        others = [
            profile(2, labels=("EMI",)),
            profile(3, genres=("Rock",)),
            profile(4, genres=("Rock", "Pop")),
        ]

        assert ids(rank_similar(target, others)) == [4, 3, 2]

    def test_genres_ignore_case_and_surrounding_spaces(self) -> None:
        target = profile(1, genres=("Art Rock",))

        ranked = rank_similar(target, [profile(2, genres=("art rock",))])

        assert ids(ranked) == [2]

    def test_label_and_composer_count(self) -> None:
        target = profile(1, labels=("Island",), composers=("Brian Eno",))
        others = [profile(2, labels=("island",)), profile(3, composers=("BRIAN ENO",))]

        assert sorted(ids(rank_similar(target, others))) == [2, 3]

    def test_era_alone_is_too_weak_to_suggest(self) -> None:
        target = profile(1, year=1977)

        assert rank_similar(target, [profile(2, year=1977)]) == []

    def test_era_breaks_ties_between_equal_matches(self) -> None:
        target = profile(1, year=1977, genres=("Rock",))
        others = [
            profile(2, year=2010, genres=("Rock",)),
            profile(3, year=1975, genres=("Rock",)),
        ]

        assert ids(rank_similar(target, others)) == [3, 2]

    def test_nothing_in_common_gives_nothing(self) -> None:
        target = profile(1, genres=("Rock",), labels=("A",), year=1977)

        assert rank_similar(target, [profile(2, genres=("Jazz",), labels=("B",), year=2001)]) == []

    def test_albums_without_tags_are_never_suggested(self) -> None:
        assert rank_similar(profile(1, genres=("Rock",)), [profile(2)]) == []


class TestReasons:
    def test_reasons_name_what_is_shared_using_the_target_spelling(self) -> None:
        target = profile(
            1,
            year=1977,
            genres=("Rock", "Ambient"),
            labels=("Island",),
            composers=("Brian Eno",),
        )
        other = profile(
            2,
            year=1975,
            genres=("ambient", "rock", "Pop"),
            labels=("ISLAND",),
            composers=("brian eno",),
        )

        [match] = rank_similar(target, [other])

        assert match.reasons == [
            "Shared genres: Ambient and Rock",
            "Same label: Island",
            "Same composer: Brian Eno",
            "Similar era: 1975",
        ]

    def test_single_genre_reads_naturally(self) -> None:
        [match] = rank_similar(profile(1, genres=("Rock",)), [profile(2, genres=("rock",))])

        assert match.reasons == ["Shared genre: Rock"]

    def test_era_is_only_a_reason_within_five_years(self) -> None:
        target = profile(1, year=1977, genres=("Rock",))

        near = rank_similar(target, [profile(2, year=1982, genres=("Rock",))])[0]
        far = rank_similar(target, [profile(3, year=1983, genres=("Rock",))])[0]

        assert near.reasons[-1] == "Similar era: 1982"
        assert far.reasons == ["Shared genre: Rock"]


class TestLimit:
    def test_limits_the_number_of_suggestions(self) -> None:
        target = profile(1, genres=("Rock",))
        others = [profile(n, genres=("Rock",)) for n in range(2, 20)]

        assert len(rank_similar(target, others, limit=6)) == 6

    def test_ties_fall_back_to_title_then_id(self) -> None:
        target = profile(1, genres=("Rock",))
        others = [
            profile(3, title="B", genres=("Rock",)),
            profile(2, title="A", genres=("Rock",)),
            profile(4, title="A", genres=("Rock",)),
        ]

        assert ids(rank_similar(target, others)) == [2, 4, 3]
