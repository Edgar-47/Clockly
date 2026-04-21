import 'package:equatable/equatable.dart';

enum TicketStatus { pending, approved, rejected, reimbursed }

enum TicketCategory { expense, purchase, travel, other }

class TicketEntity extends Equatable {
  const TicketEntity({
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
  final TicketCategory category;
  final TicketStatus status;
  final DateTime date;
  final DateTime createdAt;
  final String? description;
  final String? mediaUrl;
  final String? mediaType; // 'image' | 'pdf'
  final int? reviewedByAdminId;
  final DateTime? reviewedAt;
  final String? reviewNote;
  final String? employeeName;

  bool get isPending => status == TicketStatus.pending;
  bool get isApproved => status == TicketStatus.approved;
  bool get canBeReviewed => status == TicketStatus.pending;

  @override
  List<Object?> get props => [id, businessId, userId, status, date];
}
