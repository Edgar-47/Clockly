import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exceptions.dart';
import '../../../data/models/ticket/ticket_model.dart';
import '../../../providers/app_providers.dart';
import '../../auth/providers/auth_provider.dart';

class TicketsState {
  const TicketsState({
    this.tickets = const [],
    this.loading = false,
    this.actionLoading = false,
    this.error,
    this.filterStatus,
    this.filterFrom,
    this.filterTo,
  });

  final List<TicketModel> tickets;
  final bool loading;
  final bool actionLoading;
  final String? error;
  final String? filterStatus;
  final DateTime? filterFrom;
  final DateTime? filterTo;

  TicketsState copyWith({
    List<TicketModel>? tickets,
    bool? loading,
    bool? actionLoading,
    String? error,
    String? filterStatus,
    DateTime? filterFrom,
    DateTime? filterTo,
    bool clearError = false,
    bool clearFilter = false,
  }) =>
      TicketsState(
        tickets: tickets ?? this.tickets,
        loading: loading ?? this.loading,
        actionLoading: actionLoading ?? this.actionLoading,
        error: clearError ? null : (error ?? this.error),
        filterStatus: clearFilter ? null : (filterStatus ?? this.filterStatus),
        filterFrom: clearFilter ? null : (filterFrom ?? this.filterFrom),
        filterTo: clearFilter ? null : (filterTo ?? this.filterTo),
      );
}

class TicketsNotifier extends AsyncNotifier<TicketsState> {
  @override
  Future<TicketsState> build() async {
    final auth = await ref.watch(authProvider.future);
    if (!auth.isAuthenticated) return const TicketsState();
    return _load();
  }

  Future<TicketsState> _load({
    String? status,
    DateTime? from,
    DateTime? to,
  }) async {
    try {
      final auth = ref.read(authProvider).valueOrNull;
      final businessId = auth?.session?.activeBusinessId;
      final datasource = ref.read(ticketDatasourceProvider);
      final tickets = await datasource.getTickets(
        businessId: businessId,
        status: status,
        from: from,
        to: to,
      );
      return TicketsState(
        tickets: tickets,
        filterStatus: status,
        filterFrom: from,
        filterTo: to,
      );
    } catch (e) {
      return TicketsState(error: _msg(e));
    }
  }

  Future<void> refresh() async {
    final current = state.valueOrNull ?? const TicketsState();
    state = AsyncValue.data(current.copyWith(loading: true, clearError: true));
    final next = await _load(
      status: current.filterStatus,
      from: current.filterFrom,
      to: current.filterTo,
    );
    state = AsyncValue.data(next);
  }

  Future<void> applyFilter({
    String? status,
    DateTime? from,
    DateTime? to,
  }) async {
    final current = state.valueOrNull ?? const TicketsState();
    state = AsyncValue.data(current.copyWith(loading: true));
    final next = await _load(status: status, from: from, to: to);
    state = AsyncValue.data(next);
  }

  Future<bool> createTicket({
    required String title,
    required double amount,
    required String category,
    required DateTime date,
    String? description,
  }) async {
    final current = state.valueOrNull ?? const TicketsState();
    state = AsyncValue.data(current.copyWith(actionLoading: true, clearError: true));
    try {
      final datasource = ref.read(ticketDatasourceProvider);
      final ticket = await datasource.createTicket(
        title: title,
        amount: amount,
        category: category,
        date: date,
        description: description,
      );
      final updated = [ticket, ...current.tickets];
      state = AsyncValue.data(current.copyWith(tickets: updated, actionLoading: false));
      return true;
    } catch (e) {
      state = AsyncValue.data(current.copyWith(actionLoading: false, error: _msg(e)));
      return false;
    }
  }

  Future<bool> reviewTicket({
    required int ticketId,
    required String status,
    String? reviewNote,
  }) async {
    final current = state.valueOrNull ?? const TicketsState();
    state = AsyncValue.data(current.copyWith(actionLoading: true, clearError: true));
    try {
      final datasource = ref.read(ticketDatasourceProvider);
      final updated = await datasource.reviewTicket(
        ticketId: ticketId,
        status: status,
        reviewNote: reviewNote,
      );
      final list = current.tickets
          .map((t) => t.id == ticketId ? updated : t)
          .toList();
      state = AsyncValue.data(current.copyWith(tickets: list, actionLoading: false));
      return true;
    } catch (e) {
      state = AsyncValue.data(current.copyWith(actionLoading: false, error: _msg(e)));
      return false;
    }
  }

  String _msg(Object e) {
    if (e is AppException) return e.userMessage;
    return 'Error en tickets.';
  }
}

final ticketsProvider = AsyncNotifierProvider<TicketsNotifier, TicketsState>(
  TicketsNotifier.new,
);
