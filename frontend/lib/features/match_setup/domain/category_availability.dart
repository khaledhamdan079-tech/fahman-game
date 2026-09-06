class CategoryAvailability {
  const CategoryAvailability({
    required this.id,
    required this.name,
    required this.description,
    required this.unused200,
    required this.unused400,
    required this.unused600,
    required this.completeMatches,
    required this.eligible,
  });

  factory CategoryAvailability.fromJson(Map<String, dynamic> json) =>
      CategoryAvailability(
        id: json['id'] as String,
        name: json['name_ar'] as String,
        description: json['description_ar'] as String? ?? '',
        unused200: json['unused_200'] as int,
        unused400: json['unused_400'] as int,
        unused600: json['unused_600'] as int,
        completeMatches: json['complete_matches_possible'] as int,
        eligible: json['eligible'] as bool,
      );

  final String id;
  final String name;
  final String description;
  final int unused200;
  final int unused400;
  final int unused600;
  final int completeMatches;
  final bool eligible;

  int get totalUnused => unused200 + unused400 + unused600;
}
