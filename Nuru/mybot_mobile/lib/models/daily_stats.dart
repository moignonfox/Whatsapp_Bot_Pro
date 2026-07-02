class DailyStats {
  final int ordersCount;
  final double revenue;
  final int cancellations;
  final int pendingCount;
  final String periodLabel;

  DailyStats({
    required this.ordersCount,
    required this.revenue,
    required this.cancellations,
    required this.pendingCount,
    this.periodLabel = "Aujourd'hui",
  });

  factory DailyStats.fromJson(Map<String, dynamic> json) {
    return DailyStats(
      ordersCount: json['orders_count'] ?? 0,
      revenue: (json['revenue'] ?? 0).toDouble(),
      cancellations: json['cancellations'] ?? 0,
      pendingCount: json['pending_count'] ?? 0,
      periodLabel: json['period_label'] ?? "Aujourd'hui",
    );
  }
}

