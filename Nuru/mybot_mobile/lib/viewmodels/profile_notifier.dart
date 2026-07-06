import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/business_profile.dart';
import '../repositories/profile_repository.dart';

final profileNotifierProvider = AsyncNotifierProvider<ProfileNotifier, BusinessProfile?>(ProfileNotifier.new);

class ProfileNotifier extends AsyncNotifier<BusinessProfile?> {
  @override
  FutureOr<BusinessProfile?> build() async {
    return _fetchProfile();
  }

  Future<BusinessProfile?> _fetchProfile() async {
    final repository = ref.watch(profileRepositoryProvider);
    return repository.getProfile();
  }

  Future<void> fetchProfile({bool silent = false}) async {
    if (!silent) state = const AsyncValue.loading();
    try {
      final profile = await _fetchProfile();
      state = AsyncValue.data(profile);
    } catch (e, st) {
      if (!silent) state = AsyncValue.error(e, st);
    }
  }

  Future<bool> updateProfile(Map<String, dynamic> data) async {
    try {
      final repository = ref.read(profileRepositoryProvider);
      final success = await repository.updateProfile(data);
      if (success) {
        await fetchProfile();
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }
}

