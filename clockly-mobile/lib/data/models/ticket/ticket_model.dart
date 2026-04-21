import '../../../domain/entities/ticket_entity.dart';

class TicketModel {
  const TicketModel({
    required this.id,
    required this.businessId,
    required this.userId,
    required this.title,
    required this.amount,
    required this.category,
    required this.status,
    required this.date,
    required this.createdAt,
    this.description,
    this.mediaUrl,
    this.mediaType,
    this.reviewedByAdminId,
    this.reviewedAt,
    this.reviewNote,
    this.employeeName,
  });

  final int id;
  final String businessId;
  final int userId;
  final String title;
  final double amount;
  final String category;
  final String status;
  final DateTime date;
  final DateTime createdAt;
  final String? description;
  final String? mediaUrl;
  final String? mediaType;
  final int? reviewedByAdminId;
  final DateTime? reviewedAt;
  final String? reviewNote;
  final String? employeeName;

  factory TicketModel.fromJson(Map<String, dynamic> json) => TicketModel(
        id: json['id'] as int,
        businessId: json['business_id']?.toString() ?? '',
        userId: json['user_id'] as int? ?? 0,
        title: (json['title'] ?? json['name'] ?? '') as String,
        amount: (json['amount'] as num?)?.toDouble() ?? 0.0,
        category: (json['category'] ?? 'other') as String,
        status: (json['status'] ?? 'pending') as String,
        date: DateTime.parse((json['date'] ?? json['created_at']) as String),
        createdAt: DateTime.parse((json['created_at'] ?? json['date']) as String),
        description: json['description'] as String?,
        mediaUrl: json['media_url'] as String?,
        mediaType: json['media_type'] as String?,
        reviewedByAdminId: json['reviewed_by_admin_id'] as int?,
        reviewedAt: json['reviewed_at'] != null
            ? DateTime.tryParse(json['reviewed_at'] as String)
            : null,
        reviewNote: json['review_note'] as String?,
        employeeName: (json['employee_name'] ?? json['user_name']) as String?,
      );

  TicketEntity toEntity() => TicketEntity(
        id: id,
        businessId: businessId,
        userId: userId,
        title: title,
        amount: amount,
        category: _parseCategory(category),
        status: _parseStatus(status),
        date: date,
        createdAt: createdAt,
        description: description,
        mediaUrl: mediaUrl,
        mediaType: mediaType,
        reviewedByAdminId: reviewedByAdminId,
        reviewedAt: reviewedAt,
        reviewNote: reviewNote,
        employeeName: employeeName,
      );

  static TicketStatus _parseStatus(String s) => switch (s) {
        'approved' => TicketStatus.approved,
        'rejected' => TicketStatus.rejected,
        'reimbursed' => TicketStatus.reimbursed,
        _ => TicketStatus.pending,
      };

  static TicketCategory _parseCategory(String c) => switch (c) {
        'expense' => TicketCategory.expense,
        'purchase' => TicketCategory.purchase,
        'travel' => TicketCategory.travel,
        _ => TicketCategory.other,
      };
}
